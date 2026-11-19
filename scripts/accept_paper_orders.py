"""Reproduce a bounded P11 order scenario against the locally imported P10 data."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.dataset_api import store
from backend.orders import OrderCommand, OrderReplayRequest
from backend.order_api import replay


def main():
    meta=json.loads(Path('docs/minute-data-p10.json').read_text())['dataset']
    start=int(datetime(2024,1,5,12,7,tzinfo=timezone.utc).timestamp())
    commands=[
        OrderCommand(command_id='buy',order_id='buy',action='submit',time=start,side='buy',kind='market',units=1000),
        OrderCommand(command_id='sell',order_id='sell',action='submit',time=start,side='sell',kind='market',units=1000),
        OrderCommand(command_id='limit',order_id='limit',action='submit',time=start,side='buy',kind='limit',units=1000,price=.5),
        OrderCommand(command_id='cancel',order_id='limit',action='cancel',time=start+60),
    ]
    body=OrderReplayRequest(dataset_id=meta['id'],start=start,clock=start+300,input_price_basis='bid',commands=commands)
    result=replay(store(),body)
    assert result==replay(store(),body)
    assert len(result['positions'])==2
    assert result['orders'][2]['status']=='cancelled'
    assert all(p['bar_open_time']>=start and p['opened_at']<=body.clock for p in result['positions'])
    early=body.model_copy(update={'clock':start,'commands':commands[:3]})
    assert not replay(store(),early)['positions']
    report={'phase':'P11','scenario':'Real P10 EUR/USD minute data; market buy/sell and cancelled limit',
            'repeatability':'passed','submission_clock_has_no_fill':'passed','result':result}
    Path('docs/paper-orders-p11.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Real-minute order acceptance passed: two entry lots, one cancelled limit, deterministic replay.')

if __name__=='__main__':main()
