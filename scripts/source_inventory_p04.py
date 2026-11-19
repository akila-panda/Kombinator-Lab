"""Record P04 adaptations without rewriting historical P01 provenance evidence."""
from pathlib import Path
import json,hashlib,sys
root=Path(__file__).resolve().parents[1]
upstream=Path(sys.argv[1]).resolve()
base=json.loads((root/'docs/source-inventory-p01.json').read_text())
changes={
 'backend/vendor/struct/atr_utils.py':'Canonical Wilder ATR wrapper replaces rolling mean',
 'backend/vendor/struct/bos_engine.py':'Accept shared ATR scalar; detector body otherwise retained',
 'backend/vendor/fxdesk/indicators.py':'Re-export canonical EMA/ATR/RSI; remove shadowed pivot_idx',
 'backend/vendor/fxdesk/zones.py':'Inject shared ATR series for FVG/OB',
 'backend/vendor/fxdesk/patterns.py':'Inject shared ATR scalar for S/R',
 'backend/vendor/scalper.py':'Inject shared EMA; exact EMA output; equal EMAs neutral and unaligned',
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for row in base['entries']:
    local=root/row['local'];original=upstream/row['upstream']
    current=sha(local)
    assert sha(original)==row['upstream_sha256'],'Upstream archive extract changed'
    if row['local'] not in changes:assert current==row['local_sha256'],row['local']
    rows.append({'local':row['local'],'upstream':row['upstream'],'local_sha256':current,'upstream_sha256':sha(original),'change_since_p01':changes.get(row['local'],'unchanged since P01')})
regime=upstream/'forex-scalper-agent-v2-main/analysis/regime_detector.py'
rows.append({'local':'backend/adapters.py','upstream':str(regime.relative_to(upstream)),'local_sha256':sha(root/'backend/adapters.py'),'upstream_sha256':sha(regime),'change_since_p01':'Adapt only ATR volatility branch (1.5/0.6 thresholds); canonical ATR; no ADX/ML/confidence'})
(root/'docs/source-inventory-p04.json').write_text(json.dumps({'phase':'P04','date':'2026-11-11','entries':rows},indent=2)+'\n')
print(f'P04 provenance recorded: {len(rows)} mappings; unchanged P01 files and upstream hashes checked.')
