import pytest
import torch
from src.config import TARGETS, read_config
from src.inference import analyze_complaint, predict_batch, batch_frame
from src.model_loader import load_model
from src.utils import normalize_kazakh, validate_text, read_upload, csv_bytes
import pandas as pd


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
    assert sum(p.numel() for p in bundle.model.parameters())==83462415
    assert bundle.model.dropout.p==.2
    inputs=bundle.tokenizer(['Қазақша шағым','Оқу ақысы төленді.'],padding=True,return_tensors='pt')
    with torch.inference_mode():outputs=bundle.model(inputs['input_ids'],inputs['attention_mask'])
    assert [tuple(x.shape) for x in outputs]==[(2,3),(2,3),(2,3),(2,6)]
    assert bundle.config['targets']==list(TARGETS)
    assert bundle.config['label_maps']['urgency']=={'high':0,'low':1,'medium':2}
    assert bundle.config['label_maps']['department']['security_ombudsperson']==4

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
    from transformers import RobertaTokenizerFast
    from src.config import MODEL_DIR
    original=RobertaTokenizerFast.from_pretrained(str(MODEL_DIR),local_files_only=True)
    texts=['Қазақша шағым: оқу ақысы төленді.','Жатақханада ыстық су жоқ.']
    expected=original(texts,padding=True,truncation=True,max_length=96)
    actual=bundle.tokenizer(texts,padding=True,truncation=True,max_length=96)
    assert actual['input_ids']==expected['input_ids']
    assert actual['attention_mask']==expected['attention_mask']


def test_csv_export_column_collision():
    from src.utils import combine_batch_export
    source=pd.DataFrame({'ai_row':[42],'=formula':['original']})
    output=combine_batch_export(source,pd.DataFrame({'row':[1]}))
    assert output.ai_row.tolist()==[42]
    assert output.ai_ai_row.tolist()==[1]
    assert "'=formula" in csv_bytes(output).decode('utf-8-sig')
