import json
import math
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import pytest
import torch
from src.config import TARGETS, read_config
from src.inference import analyze_complaint, predict_batch, batch_frame
from src.model_loader import load_model
from src.utils import normalize_kazakh, validate_text, read_upload, csv_bytes
import pandas as pd

EXAMPLES = json.loads((Path(__file__).parents[1] / 'data/multilingual_examples.json').read_text())


@pytest.mark.model
@pytest.mark.parametrize('example', EXAMPLES, ids=lambda e: e['language'])
def test_multilingual_real_inference(bundle, example):
    result = analyze_complaint(bundle, example['text'])
    assert result['text'] == example['text']
    assert result['normalized_text'] == example['text']
    assert not result['truncated']
    assert result['predictions']['department'] == 'finance_office'
    for task in TARGETS:
        probabilities = result['probabilities'][task]
        assert set(probabilities) == set(bundle.config['label_names'][task])
        assert all(math.isfinite(p) and 0 <= p <= 1 for p in probabilities.values())
        assert sum(probabilities.values()) == pytest.approx(1, abs=1e-6)
    assert result['requires_review'] == (
        result['routing_confidence'] < .75 or result['high_urgency_probability'] >= .30
    )


@pytest.mark.model
def test_multilingual_batch_matches_single(bundle):
    texts = [e['text'] for e in EXAMPLES]
    batch = predict_batch(bundle, texts)
    for text, result in zip(texts, batch):
        single = analyze_complaint(bundle, text)
        assert result['predictions'] == single['predictions']
        for task in TARGETS:
            assert result['probabilities'][task] == pytest.approx(single['probabilities'][task], abs=1e-5)


@pytest.mark.model
def test_named_heads_and_exported_indices_control_decoding(bundle):
    text = EXAMPLES[0]['text']
    original = analyze_complaint(bundle, text)
    config = deepcopy(bundle.config)
    config['tasks'].reverse()
    # An alternative ordered taxonomy must relabel the same numeric columns.
    for task in TARGETS:
        names = config['label_names'][task]
        config['label_maps'][task] = {name: len(names) - 1 - i for i, name in enumerate(names)}
    result = analyze_complaint(replace(bundle, config=config), text)
    for task in TARGETS:
        names = bundle.config['label_names'][task]
        for old, new in zip(names, reversed(names)):
            assert result['probabilities'][task][new] == pytest.approx(original['probabilities'][task][old])


@pytest.mark.model
def test_streamlit_resource_cache_reuses_model(bundle):
    from src.config import MODEL_DIR
    from src.ui import cached_model
    first = cached_model(str(MODEL_DIR))
    assert cached_model(str(MODEL_DIR)) is first


def test_notebook_normalization():
    assert normalize_kazakh('  Қазақ\u200bша\ufeff\n\t мәтін  ')=='Қазақша мәтін'
    assert normalize_kazakh('и\u0306')=='й'
    assert normalize_kazakh('ӘҒҚҢӨҰҮҺІ!')=='ӘҒҚҢӨҰҮҺІ!'

@pytest.mark.parametrize('text',['','  ', '\u200b',None,float('nan'),123,'x'*10001])
def test_invalid_input(text):
    with pytest.raises(ValueError):validate_text(text)


def test_missing_model_fails(tmp_path):
    with pytest.raises(FileNotFoundError):load_model(tmp_path, allow_download=False)

@pytest.mark.model
def test_model_shape_and_mapping(bundle):
    assert not bundle.model.training
    assert next(bundle.model.parameters()).device.type=='cpu'
    assert sum(p.numel() for p in bundle.model.parameters())==278055183
    assert bundle.model.dropout.p==.2
    inputs=bundle.tokenizer(['Қазақша шағым','Оқу ақысы төленді.'],padding=True,return_tensors='pt')
    with torch.inference_mode():outputs=bundle.model(inputs['input_ids'],inputs['attention_mask'])
    assert {t: tuple(x.shape) for t, x in outputs.items()} == {
        t: (2, len(bundle.config['label_names'][t])) for t in TARGETS
    }
    assert bundle.config['targets']==list(TARGETS)
    for task in TARGETS:
        assert bundle.config['label_maps'][task] == {name: i for i, name in enumerate(bundle.config['label_names'][task])}
    assert all(t.device.type == 'cpu' for t in bundle.model.buffers())
    assert bundle.model.encoder.config.model_type == 'xlm-roberta'
    assert bundle.config['max_length'] == 128

@pytest.mark.model
def test_real_prediction_probabilities_and_batch(bundle,real_result):
    rows=predict_batch(bundle,[real_result['text'],None,' ', 'Оқу ақысын төледім, бірақ жүйеде төлем көрсетілмейді.'],batch_size=2)
    assert len(rows)==4
    assert 'error' in rows[1] and 'error' in rows[2]
    assert rows[0]['predictions']==real_result['predictions']
    for task in TARGETS:
        assert set(rows[0]['probabilities'][task])==set(bundle.config['label_maps'][task])
        assert sum(rows[0]['probabilities'][task].values())==pytest.approx(1,abs=1e-6)
        assert rows[0]['probabilities'][task]==pytest.approx(real_result['probabilities'][task],abs=1e-5)
    frame=batch_frame(rows)
    assert len(frame)==4 and {'category','urgency','tone','department','requires_review','error','row'} <= set(frame)
    assert frame.loc[1,'row']==2
    assert frame.loc[1,'error']
    assert predict_batch(bundle,[])==[]
    with pytest.raises(ValueError):analyze_complaint(bundle,' ')

@pytest.mark.model
def test_truncation_and_masked_padding(bundle):
    result=analyze_complaint(bundle,'Шағым мәтіні. '*200)
    assert result['truncated']
    short='Оқу ақысын төледім.'
    single=analyze_complaint(bundle,short)
    batched=predict_batch(bundle,[short,'Жатақханада бірнеше күннен бері ыстық су жоқ. Студенттер қатты қиналып жатыр.'])[0]
    assert single['probabilities']['category']==pytest.approx(batched['probabilities']['category'],abs=1e-5)


def test_csv_safety():
    frame=read_upload('text_kk\nҚазақша шағым\n'.encode())
    assert len(frame)==1
    for bad in [b'a\n',b'x'*(5*1024*1024+1),('a\n'+'text\n'*1001).encode()]:
        with pytest.raises(ValueError):read_upload(bad)
    output=csv_bytes(pd.DataFrame({'text':['=1+1',' @SUM(1,2)','Қазақша']})).decode('utf-8-sig')
    assert "'=1+1" in output and "' @SUM" in output

@pytest.mark.model
def test_exported_tokenizer_matches_roberta_fast(bundle):
    from transformers import XLMRobertaTokenizerFast
    from src.config import MODEL_DIR
    original=XLMRobertaTokenizerFast.from_pretrained(str(MODEL_DIR),local_files_only=True)
    texts=['Қазақша шағым: оқу ақысы төленді.','Жатақханада ыстық су жоқ.'] + [e['text'] for e in EXAMPLES]
    expected=original(texts,padding=True,truncation=True,max_length=bundle.config['max_length'])
    actual=bundle.tokenizer(texts,padding=True,truncation=True,max_length=bundle.config['max_length'])
    assert actual['input_ids']==expected['input_ids']
    assert actual['attention_mask']==expected['attention_mask']


def test_csv_export_column_collision():
    from src.utils import combine_batch_export
    source=pd.DataFrame({'ai_row':[42],'=formula':['original']})
    output=combine_batch_export(source,pd.DataFrame({'row':[1]}))
    assert output.ai_row.tolist()==[42]
    assert output.ai_ai_row.tolist()==[1]
    assert "'=formula" in csv_bytes(output).decode('utf-8-sig')
