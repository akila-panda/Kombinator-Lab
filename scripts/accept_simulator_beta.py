"""P16 real-history acceptance on a temporary store; never mutate user sessions."""
import hashlib,json,platform,statistics,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.datasets import DatasetStore
from backend.replay_api import ReplayRequest,replay_state,completed_analysis
from backend.accounting import AccountCommand,AccountReplayRequest
from backend.order_api import account_replay
from backend.sessions import Save,save,read,branch,Branch,review


def main():
    source=Path('.data/p10/eurusd-2024-01-02-08-bid-m1.csv')
    raw=source.read_bytes()
    manifest=json.loads(Path('docs/minute-data-p10.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==manifest['csv_sha256']
    with tempfile.TemporaryDirectory(prefix='confluence-p16-') as tmp:
        db=DatasetStore(tmp)
        meta=db.import_csv(raw,symbol='EUR/USD',base_timeframe='1m',calendar='fx-ny-17-v1',input_timezone='UTC',timestamp_unit='seconds',volume_type='unknown',source_label='P16 isolated real history')
        start=1704456420
        def state(clock):return replay_state(db,ReplayRequest(dataset_id=meta['id'],clock=clock))
        completed_analysis.cache_clear()
        timings=[]
        for i in range(12):
            t=time.perf_counter();result=state(start+i*60);timings.append((time.perf_counter()-t)*1000)
            assert result['clock']==start+i*60
            assert result['analysis']['contract']['snapshot']['as_of']<=result['clock']
            assert all(e['available_at']<=result['clock'] for e in result['analysis']['contract']['evidence'])
        assert state(start)==state(start)
        assert state(1704542400)['state']=='closed_market'
        assert state(meta['end'])['state']=='ended'
        try:state(1640995200)
        except ValueError:pass
        else:raise AssertionError('2022 outside coverage accepted')
        cmds=[AccountCommand(command_id='buy',order_id='one',action='submit',time=start,side='buy',kind='market',units=10000,stop_loss=1.08,take_profit=1.12),AccountCommand(command_id='partial',order_id='one',action='close',time=start+60,units=4000),AccountCommand(command_id='close',order_id='one',action='close',time=start+120)]
        req=AccountReplayRequest(dataset_id=meta['id'],start=start,clock=start+300,input_price_basis='bid',commands=cmds)
        account=account_replay(db,req)
        assert account==account_replay(db,req)
        assert [e['units'] for e in account['events'] if e['type']=='closed']==[4000,6000]
        parent=save(db,Save(label='P16 disposable acceptance',request=req,notes=[dict(order_id='one',kind='entry',text='P16 real-history example')]))
        restored=read(DatasetStore(tmp),parent['id']);assert restored==parent
        child=branch(parent['id'],Branch(clock=start+60),db)
        assert child['parent_id']==parent['id'] and read(db,parent['id'])==parent
        assert review(parent['id'],db)['read_only']
        report=dict(date='2026-11-18',runtime=dict(python=platform.python_version(),platform=platform.platform(),machine=platform.machine()),data=dict(sha256=manifest['csv_sha256'],rows=meta['count'],start=meta['start'],end=meta['end']),checks=['real-history deterministic replay','evidence availability','closed market','end of data','out-of-range rejection','partial/full closes','fresh-store restore','immutable branch parent','read-only review'],performance=dict(measurement='direct replay_state wall time; one process; not HTTP or browser latency',samples_ms=timings,cold_ms=timings[0],median_ms=statistics.median(timings),max_ms=max(timings)),account=account['account'])
        Path('docs/simulator-beta-p16.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
if __name__=='__main__':main()
