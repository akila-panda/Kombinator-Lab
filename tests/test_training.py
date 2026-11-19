from backend.training import summary
from backend.accounting import execute_account,AccountCommand,AccountSettings
from backend.sessions import Save,save,branch,Branch,read,review
from backend.datasets import DatasetStore
from backend.accounting import AccountReplayRequest
from fastapi import HTTPException
import pytest
T=1704153600

def test_branch_review_and_blind_guard(tmp_path):
 db=DatasetStore(tmp_path)
 rows=[dict(time=T+i*60,open=1.1+i*.001,high=1.1+i*.001,low=1.1+i*.001,close=1.1+i*.001,volume=None) for i in range(3)]
 meta=db.save(rows,symbol='EUR/USD',base_timeframe='1m',calendar='fixed-utc-v1',source_kind='synthetic',source_label='training fixture')
 commands=[AccountCommand(command_id='a',order_id='a',time=T,action='submit',kind='market',side='buy',units=1000),AccountCommand(command_id='b',order_id='a',time=T+60,action='close')]
 req=AccountReplayRequest(dataset_id=meta['id'],start=T,clock=T+180,input_price_basis='bid',commands=commands)
 parent=save(db,Save(label='parent',request=req))
 child=branch(parent['id'],Branch(clock=T+60),db)
 assert child['account']['positions'][0]['remaining_units']==1000
 assert child['account']['pending_closes']
 assert read(db,parent['id'])==parent
 report=review(parent['id'],db)['summary']
 assert report['wins']==1 and report['closed_trades']==1
 assert report['net_realized_after_costs']=='0.82'
 assert report['max_balance_drawdown']=='0.04'
 blind=save(db,Save(label='blind',request=req,mode='blind'))
 with pytest.raises(HTTPException):branch(blind['id'],Branch(clock=T+60),db)
 assert review(parent['id'],db)['read_only']
