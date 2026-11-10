import math


def route(probabilities, config):
    confidence = min(max(probabilities[t].values()) for t in ('category', 'urgency', 'department'))
    p_high = probabilities['urgency']['high']
    if not all(math.isfinite(p) and 0 <= p <= 1 for values in probabilities.values() for p in values.values()):
        raise ValueError('Model produced invalid probabilities.')
    reasons = []
    if confidence < config['confidence_threshold']:
        reasons.append('Low prediction confidence')
    if p_high >= config['urgent_review_threshold']:
        reasons.append('Potentially high urgency')
    urgency = max(probabilities['urgency'], key=probabilities['urgency'].get)
    return {
        'routing_confidence': confidence, 'high_urgency_probability': p_high,
        'requires_review': bool(reasons),
        'review_reasons': reasons or ['Eligible for automatic routing'],
        'operational_priority': 'high' if p_high >= config['urgent_review_threshold'] else urgency,
        'suggested_sla_hours': config['sla_hours'][urgency],
        'confidence_threshold': config['confidence_threshold'],
        'urgent_review_threshold': config['urgent_review_threshold'],
    }
