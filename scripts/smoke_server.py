"""Exercise a real local HTTP server on an OS-assigned port; always shut it down."""
from pathlib import Path
import json
import tempfile
from unittest.mock import patch
from datetime import datetime,timezone
import re
import socket
import sys
import threading
import time
from urllib.request import Request, build_opener, ProxyHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import uvicorn
from backend.main import app
from backend.analysis import demo
from backend.dataset_api import store
from backend.datasets import DatasetStore
from backend.sentiment import ArchiveStore


def main():
    temporary=tempfile.TemporaryDirectory(prefix='confluence-smoke-')
    db=DatasetStore(temporary.name)
    archive_patch=patch('backend.sentiment.archive_store',return_value=ArchiveStore(temporary.name))
    archive_patch.start()
    app.dependency_overrides[store]=lambda:db
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    url = f'http://127.0.0.1:{sock.getsockname()[1]}'
    server = uvicorn.Server(uvicorn.Config(app, log_level='error'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    opener = build_opener(ProxyHandler({}))
    try:
        thread.start()
        deadline = time.monotonic() + 15
        while not server.started:
            if not thread.is_alive() or time.monotonic() >= deadline:
                raise RuntimeError('Local server failed to start within 15 seconds')
            time.sleep(.05)
        def get(path):
            with opener.open(url+path, timeout=15) as response:
                assert response.status == 200
                return response.read()
        assert json.loads(get('/api/health'))['status'] == 'ok'
        page = get('/').decode()
        assert 'Confluence' in page
        assets = re.findall(r'(?:src|href)="(/assets/[^\"]+)"', page)
        assert assets, 'Built frontend assets missing'
        for asset in assets:
            assert get(asset)
        body = {'symbol': 'EUR/USD', 'interval': '1h', 'candles': demo('EUR/USD')[:200]}
        request = Request(url+'/api/analyze', data=json.dumps(body).encode(), headers={'Content-Type':'application/json'})
        with opener.open(request, timeout=15) as response:
            result = json.load(response)
        assert len(result['modules']) == 4 and len(result['candles']) == 200
        csv='time,open,high,low,close\n'+'\n'.join(','.join(str(c[k]) for k in ['time','open','high','low','close']) for c in body['candles'])
        request=Request(url+'/api/datasets/import?symbol=EUR%2FUSD&base_timeframe=1h&calendar=utc-weekdays-v1&source_label=synthetic-smoke-fixture',data=csv.encode(),headers={'Content-Type':'text/csv'})
        with opener.open(request,timeout=15) as response:meta=json.load(response)
        assert meta['count']==200 and meta['source_kind']=='user_upload'
        assert json.loads(get('/api/datasets/'+meta['id']))['id']==meta['id']
        query={'dataset_id':meta['id'],'cutoff':150,'interval':'1h'}
        request=Request(url+'/api/datasets/analyze',data=json.dumps(query).encode(),headers={'Content-Type':'application/json'})
        with opener.open(request,timeout=15) as response:result=json.load(response)
        assert len(result['candles'])==150 and result['contract']['snapshot']['calendar']=='utc-weekdays-v1'
        assert result['contract']['retrospective_findings_only']
        journal=json.loads(get('/api/datasets/'+meta['id']+'/events?as_of='+str(result['historical']['as_of'])))
        assert journal['status']=='available' and journal['events']
        assert all(e['available_at']<=result['historical']['as_of'] for e in journal['events'])
        assert len(json.loads(get('/api/datasets/'+meta['id']+'/candles?limit=5'))['candles'])==5
        clock=result['historical']['as_of']
        time_iso=datetime.fromtimestamp(clock,timezone.utc).isoformat()
        archive={'label':'synthetic smoke book','snapshots':[{'instrument':'EUR_USD','positionBook':{'time':time_iso,'retrieved_at':time_iso,'buckets':[{'price':1.08,'longCountPercent':80,'shortCountPercent':20}]}}]}
        request=Request(url+'/api/sentiment/archives',data=json.dumps(archive).encode(),headers={'Content-Type':'application/json'})
        with opener.open(request,timeout=15) as response:book_archive=json.load(response)
        scored=json.loads(get('/api/sentiment/archives/'+book_archive['id']+'/at?symbol=EUR%2FUSD&as_of='+str(clock)))
        assert scored['status']=='available' and scored['source_id']=='archive:'+book_archive['id']
        assert json.loads(get('/api/sentiment/archives/'+book_archive['id']+'/at?symbol=EUR%2FUSD&as_of='+str(clock-1)))['status']=='unavailable'
        minute_start=1704153600
        minute_rows=[dict(time=minute_start+i*60,open=1.1,high=1.101,low=1.099,close=1.1,volume=None) for i in range(3)]
        minute_meta=db.save(minute_rows,symbol='EUR/USD',base_timeframe='1m',calendar='fixed-utc-v1',source_kind='synthetic',source_label='paper HTTP fixture')
        paper={'dataset_id':minute_meta['id'],'start':minute_start,'clock':minute_start+120,'input_price_basis':'bid','commands':[{'command_id':'buy','order_id':'one','action':'submit','time':minute_start+60,'side':'buy','kind':'market','units':1000}]}
        request=Request(url+'/api/paper/replay',data=json.dumps(paper).encode(),headers={'Content-Type':'application/json'})
        with opener.open(request,timeout=15) as response:execution=json.load(response)
        assert execution['positions'][0]['entry_price']=='1.10010'
        assert execution['positions'][0]['bar_open_time']==minute_start+60
        assert execution['events'][-1]['time']==minute_start+120
        paper['commands'].append({'command_id':'close','order_id':'one','action':'close','time':minute_start+120})
        paper['clock']=minute_start+180
        request=Request(url+'/api/paper/account-replay',data=json.dumps(paper).encode(),headers={'Content-Type':'application/json'})
        with opener.open(request,timeout=15) as response:account=json.load(response)
        assert account['positions'][0]['remaining_units']==0
        assert account['account']['balance']=='9999.82'
        assert account['account']['commission_paid']=='0.08'
        assert account['account']['used_margin']=='0.00'
        print('HTTP smoke passed: startup, assets, legacy analysis, CSV import, stored metadata, paginated range, dataset-ID analysis causal event journal and clock-bounded sentiment archive and paper-order/account execution.')

    finally:
        server.should_exit = True
        if thread.ident is not None: thread.join(timeout=10)
        sock.close()
        if thread.is_alive(): raise RuntimeError('Temporary server did not shut down')
        app.dependency_overrides.pop(store,None)
        archive_patch.stop()
        temporary.cleanup()


if __name__ == '__main__': main()
