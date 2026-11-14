import torch
from src.config import TARGETS
from src.routing import route
from src.utils import validate_text


def predict_batch(bundle, texts, batch_size=4, progress=None):
    """One forward pass per batch; invalid rows retain their input positions."""
    if not 1 <= batch_size <= 64:
        raise ValueError('Batch size must be between 1 and 64.')
    results = [None] * len(texts)
    valid = []
    for index, text in enumerate(texts):
        try:
            valid.append((index, text, validate_text(text)))
        except ValueError as exc:
            results[index] = {'error': str(exc), 'row': index + 1}
    with bundle.lock, torch.inference_mode():
        for start in range(0, len(valid), batch_size):
            part = valid[start:start + batch_size]
            inputs = bundle.tokenizer([v[2] for v in part], return_tensors='pt', padding=True, truncation=True, max_length=bundle.config['max_length'])
            logits = bundle.model(inputs['input_ids'], inputs['attention_mask'])
            probabilities = {task: torch.softmax(output.float(), dim=1).cpu().tolist()
                             for task, output in logits.items()}
            for j, (index, original, normalized) in enumerate(part):
                distributions = {
                    task: {label: probabilities[task][j][label_id] for label, label_id in bundle.config['label_maps'][task].items()}
                    for task in bundle.config['tasks']
                }
                full_length = len(bundle.tokenizer.encode(normalized, truncation=False, verbose=False))
                results[index] = {
                    'text': original, 'normalized_text': normalized,
                    'predictions': {t: max(distributions[t], key=distributions[t].get) for t in TARGETS},
                    'probabilities': distributions, 'truncated': full_length > bundle.config['max_length'],
                    'max_length': bundle.config['max_length'],
                    **route(distributions, bundle.config),
                }
            if progress:
                progress(min(start + len(part), len(valid)) / len(valid))
    return results


def analyze_complaint(bundle, text):
    validate_text(text)
    return predict_batch(bundle, [text])[0]


def batch_frame(results):
    import pandas as pd
    rows = []
    for index, result in enumerate(results):
        row = {'row': index + 1}
        if 'error' in result:
            row['error'] = result['error']
        else:
            row.update({'text': result['text'], **result['predictions']})
            row.update({k: result[k] for k in ('routing_confidence', 'high_urgency_probability', 'requires_review', 'operational_priority', 'suggested_sla_hours', 'truncated')})
            row['review_reasons'] = '; '.join(result['review_reasons'])
            row['error'] = ''
        rows.append(row)
    return pd.DataFrame(rows)
