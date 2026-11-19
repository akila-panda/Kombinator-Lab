import pytest
from scripts.accept_real_history import decode


def fixture():
    return dict(timestamp=1704067200000,multiplier=.00001,open=1.1,high=1.2,low=1.,close=1.15,shift=3600000,times=[2,3],opens=[0,10],highs=[0,20],lows=[0,-10],closes=[0,5],volumes=[1.,2.])


def test_delta_decoding_preserves_gaps_and_price_units():
    rows=decode(fixture())
    assert len(rows)==2
    assert rows[0]['time']==1704074400 and rows[1]['time']==1704085200
    assert rows[1]==dict(time=1704085200,open=1.1001,high=1.2002,low=.9999,close=1.15005)


@pytest.mark.parametrize('key,value',[('times',[2,0]),('times',[2,-1]),('opens',[0]),('highs',[0,float('nan')]),('shift',60000),('multiplier',0)])
def test_bad_feed_is_rejected(key,value):
    d=fixture();d[key]=value
    with pytest.raises(ValueError):decode(d)
