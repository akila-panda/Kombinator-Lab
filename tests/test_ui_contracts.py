import pytest
from backend.analysis import analyze,demo
from backend.contracts import Overlay,AnalysisEnvelope


def test_backend_geometry_has_inspectable_evidence_and_categories():
    r=analyze(demo('EUR/USD'),'EUR/USD','d1',10000)
    contract=AnalysisEnvelope.model_validate(r['contract'])
    findings={f.id:f for f in contract.findings};evidence={e.id:e for e in contract.evidence}
    categories={'bias_reference','structure','structure_break','fair_value_gap','order_block','supply_demand','rsi_divergence','support_resistance'}
    assert {f.kind for f in findings.values()}<=categories
    assert any(f.kind=='support_resistance' for f in findings.values())
    for shape in contract.overlays:
        finding=findings[shape.finding_id]
        assert finding.evidence_ids and all(e in evidence for e in finding.evidence_ids)
        assert all(evidence[e].available_at<=contract.snapshot.as_of for e in finding.evidence_ids)
    for f in findings.values():
        if f.kind=='rsi_divergence':
            lines=[o for o in contract.overlays if o.finding_id==f.id]
            assert {o.pane for o in lines}=={'price','rsi'}
            assert [p.time for p in lines[0].points]==[p.time for p in lines[1].points]
        if f.kind=='support_resistance':
            assert next(o for o in contract.overlays if o.finding_id==f.id).kind=='level'
        if f.kind in ('fair_value_gap','order_block','supply_demand'):
            assert any(o.kind=='zone' and o.finding_id==f.id for o in contract.overlays)


def test_rsi_zero_and_price_bounds_are_distinct():
    valid=dict(id='rsi',finding_id='f',kind='line',pane='rsi',points=[{'time':1,'price':0.},{'time':2,'price':100.}])
    assert Overlay.model_validate(valid)
    with pytest.raises(ValueError):Overlay.model_validate(valid|{'pane':'price'})
    with pytest.raises(ValueError):Overlay.model_validate(valid|{'points':[{'time':1,'price':50.},{'time':2,'price':101.}]})
