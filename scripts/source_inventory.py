"""Record a P01 provenance snapshot. Does not modify upstream source.

Usage: .venv/bin/python scripts/source_inventory.py /path/to/extracted/repos
"""
import ast
import hashlib
import json
from pathlib import Path
import sys

project = Path(__file__).resolve().parents[1]
upstream = Path(sys.argv[1]).resolve()
entries = []
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def record(local, original, mode):
    p, q = project/local, upstream/original
    entry = {'local': local, 'upstream': original, 'mode': mode, 'local_sha256': digest(p), 'upstream_sha256': digest(q)}
    if p.suffix == '.py':
        entry['definitions'] = [n.name for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
    if mode == 'copied': assert p.read_bytes() == q.read_bytes(), f'Unexpected source change: {local}'
    entries.append(entry)

for name in ['pip_utils','zigzag_engine','structure_engine','trend_engine','zones_engine','momentum_engine','atr_utils','bos_engine','choch_engine']:
    record(f'backend/vendor/struct/{name}.py',f'Sturct-ai-main/artifacts/trading-api/services/{name}.py','signature repair' if name=='zones_engine' else 'copied')
for name in ['indicators','zones','sessions','patterns']:
    record(f'backend/vendor/fxdesk/{name}.py',f'FX-Signal-Desk-main/fxbot/{name}.py','RSI replacement' if name=='indicators' else 'copied')
record('backend/vendor/scalper.py','forex-scalper-agent-v2-main/consensus_validator.py','method extraction')
record('backend/vendor/forexdashboard.py','ForexDashboard-main/ForexDashboard.py','function/method extraction')
record('frontend/src/components/TradingChart.tsx','Sturct-ai-main/artifacts/trading-dashboard/src/components/TradingChart.tsx','EMA integration and selected-price label')
record('frontend/src/components/TopBar.ts','Sturct-ai-main/artifacts/trading-dashboard/src/components/TopBar.tsx','type extraction')
record('frontend/src/hooks/use-trading-api.ts','Sturct-ai-main/artifacts/trading-dashboard/src/hooks/use-trading-api.ts','type extraction')

def function(path, name, cls=None):
    tree=ast.parse(path.read_text())
    if cls: tree=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
    return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
checks=[]
for local,original,name,local_cls,original_cls in [
 ('backend/vendor/scalper.py','forex-scalper-agent-v2-main/consensus_validator.py','check_h1_alignment','TechnicalAlignment','ConsensusValidator'),
 ('backend/vendor/forexdashboard.py','ForexDashboard-main/ForexDashboard.py','calculate_pivot_points',None,None),
 ('backend/vendor/forexdashboard.py','ForexDashboard-main/ForexDashboard.py','analyze_orderbook','SnapshotStrategy','TradingStrategy'),
 ('backend/vendor/forexdashboard.py','ForexDashboard-main/ForexDashboard.py','analyze_positionbook','SnapshotStrategy','TradingStrategy')]:
    assert ast.dump(function(project/local,name,local_cls))==ast.dump(function(upstream/original,name,original_cls)),name
    checks.append(name)
output=project/'docs/source-inventory-p01.json'
output.write_text(json.dumps({'phase':'P01','date':'2026-11-10','entries':entries,'extracted_bodies_verified_unchanged':checks},indent=2)+'\n')
print(f'Provenance verified: {len(entries)} mapped files; {len(checks)} extracted function/method ASTs unchanged.')
