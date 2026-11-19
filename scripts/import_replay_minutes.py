"""Import bounded real minute responses without filling missing minutes."""
import json,sys,csv,io,hashlib
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.accept_real_history import decode
from backend.datasets import DatasetStore

def main(directory):
    rows=[];sources=[]
    for day in range(2,9):
        p=Path(directory)/f'2024-01-{day}.json';raw=p.read_bytes();data=json.loads(raw)
        decoded=decode(data,60000,True)
        assert all(datetime.fromtimestamp(r['time'],timezone.utc).strftime('%Y-%m-%d')==f'2024-01-{day:02d}' for r in decoded)
        rows.extend(decoded);sources.append({'url':f'https://jetta.dukascopy.com/v1/candles/minute/EUR-USD/BID/2024/1/{day}','sha256':hashlib.sha256(raw).hexdigest(),'rows':len(decoded)})
    buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=['time','open','high','low','close']);w.writeheader();w.writerows(rows)
    content=buf.getvalue().encode();folder=Path('.data/p10');folder.mkdir(parents=True,exist_ok=True);(folder/'eurusd-2024-01-02-08-bid-m1.csv').write_bytes(content)
    meta=DatasetStore('.data').import_csv(content,symbol='EUR/USD',base_timeframe='1m',calendar='fx-ny-17-v1',input_timezone='UTC',timestamp_unit='seconds',volume_type='unknown',source_label='Dukascopy EUR/USD BID M1 · 2024 Jan 2–8')
    Path('docs/minute-data-p10.json').write_text(json.dumps({'sources':sources,'csv_sha256':hashlib.sha256(content).hexdigest(),'dataset':meta,'normalization':'Observed minute bars only; no interpolation or gap filling; volume omitted.'},indent=2)+'\n')
    print(meta['id'],meta['count'],meta['quality']['missing_bars'])
if __name__=='__main__':main(sys.argv[1])
