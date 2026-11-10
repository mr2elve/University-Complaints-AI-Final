import pytest
from src.routing import route

CONFIG={'confidence_threshold':.75,'urgent_review_threshold':.30,'sla_hours':{'high':4,'medium':24,'low':72}}

def probabilities(confidence=.8,high=.1):
    # Controlled probability distributions for policy boundary testing, never application inference.
    return {'category':{'a':confidence,'b':1-confidence},'urgency':{'high':high,'medium':.85 if high==.1 else 1-high,'low':.05 if high==.1 else 0},'department':{'a':.9,'b':.1},'tone':{'a':.34,'b':.33,'c':.33}}

@pytest.mark.parametrize('confidence,high,review',[(.75,.1,False),(.74999,.1,True),(.8,.30,True),(.8,.29999,True)])
def test_thresholds(confidence,high,review):
    assert route(probabilities(confidence,high),CONFIG)['requires_review'] is review

def test_tone_excluded_and_equality_auto():
    result=route(probabilities(.75),CONFIG)
    assert result['routing_confidence']==.75
    assert not result['requires_review']

def test_high_probability_boundary_independent_of_low_confidence():
    cfg={**CONFIG,'confidence_threshold':.6}
    below=route(probabilities(.9,.29999),cfg)
    equal=route(probabilities(.9,.30),cfg)
    assert not below['requires_review']
    assert equal['requires_review']
    assert equal['operational_priority']=='high'
    assert equal['suggested_sla_hours']==24
    assert equal['review_reasons']==['Potentially high urgency']

def test_both_reasons():
    assert len(route(probabilities(.7,.3),CONFIG)['review_reasons'])==2
