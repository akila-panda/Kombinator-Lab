import pytest
from fastapi import HTTPException
from backend.datasets import DatasetStore
from backend.sessions import Save,save,read,connection
from backend.accounting import AccountReplayRequest,AccountCommand
T=1704153600

def test_checkpoint_restore_export_and_incompatibility(tmp_path):
 db=DatasetStore(tmp_path)
 meta=db.save([dict(time=T+i*60,open=1.1,high=1.101,low=1.099,close=1.1,volume=None) for i in range(3)],symbol='EUR/USD',base_timeframe='1m',calendar='fixed-utc-v1',source_kind='synthetic',source_label='session fixture')
 req=AccountReplayRequest(dataset_id=meta['id'],start=T,clock=T+120,input_price_basis='bid',commands=[AccountCommand(command_id='a',order_id='one',action='submit',time=T,side='buy',kind='market',units=1000)])
 value=save(db,Save(label='test',request=req,notes=[dict(order_id='one',kind='entry',text='Entry reason')]))
 assert read(DatasetStore(tmp_path),value['id'])==value
 assert read(db,value['id'],False)['account']['events']==value['account']['events']
 with pytest.raises(ValueError):save(db,Save(label='bad',request=req,notes=[dict(order_id='missing',kind='exit',text='x')]))
 import json
 bad={**value,'execution_version':'old'}
 with connection(db) as c:c.execute('UPDATE sessions SET payload=? WHERE id=?',(json.dumps(bad),value['id']))
 with pytest.raises(HTTPException) as e:read(db,value['id'])
 assert e.value.status_code==409
 assert read(db,value['id'],False)==bad
