"""Reproduce a P12 partial-close account against local P10 minute history."""
import json
import sys
from decimal import Decimal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.accounting import AccountCommand, AccountReplayRequest, AccountSettings
from backend.order_api import account_replay
from backend.dataset_api import store


def main():
    meta=json.loads(Path('docs/minute-data-p10.json').read_text())['dataset']
    start=1704456420 # 2024-01-05 12:07 UTC
    commands=[
        AccountCommand(command_id='buy',order_id='one',action='submit',time=start,side='buy',kind='market',units=10000,stop_loss=1.08,take_profit=1.12),
        AccountCommand(command_id='partial',order_id='one',action='close',time=start+60,units=4000),
        AccountCommand(command_id='remaining',order_id='one',action='close',time=start+120),
    ]
    request=AccountReplayRequest(dataset_id=meta['id'],start=start,clock=start+300,input_price_basis='bid',
                                 commands=commands,account=AccountSettings(slippage_pips=.5))
    result=account_replay(store(),request)
    assert result==account_replay(store(),request)
    closed=[e for e in result['events'] if e['type']=='closed']
    assert [e['units'] for e in closed]==[4000,6000]
    assert all(e['reason']=='manual' for e in closed)
    assert result['positions'][0]['remaining_units']==0
    a={k:Decimal(v) for k,v in result['account'].items()}
    assert a['balance']==10000+a['realized_pnl']-a['commission_paid']
    assert a['equity']==a['balance'] and a['used_margin']==0 and a['unrealized_pnl']==0
    Path('docs/paper-account-p12.json').write_text(json.dumps({'phase':'P12','repeatability':'passed',
         'reconciliation':'passed','scenario':'Real minute data, 10000-unit buy, 4000/6000 partial closes, fixed spread/commission/slippage',
         'result':result},indent=2)+'\n')
    print('Real-minute account acceptance passed: partial/full closes, deterministic ledger and reconciled USD balance.')

if __name__=='__main__':main()
