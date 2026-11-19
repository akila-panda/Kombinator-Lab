"""Immutable local practice checkpoints with reproducible evidence and journal."""
import hashlib,json,sqlite3,uuid
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from pydantic import Field
from .contracts import Contract,SCHEMA_VERSION
from .accounting import AccountReplayRequest,VERSION
from .order_api import account_replay
from .replay_api import ReplayRequest,replay_state
from .dataset_api import store,checked

router=APIRouter(prefix='/api/sessions')
class Note(Contract):
    order_id:str=Field(min_length=1,max_length=80)
    kind:Literal['entry','exit','review']
    text:str=Field(min_length=1,max_length=4000)
class Prediction(Contract):
    clock:int=Field(strict=True,ge=0)
    text:str=Field(min_length=1,max_length=2000)
class Save(Contract):
    mode:Literal['practice','blind']='practice'
    parent_id:str|None=None
    predictions:list[Prediction]=Field(default_factory=list,max_length=500)

    label:str=Field(min_length=1,max_length=120)
    request:AccountReplayRequest
    notes:list[Note]=Field(default_factory=list,max_length=200)

def calculation_version():
    root=Path(__file__).parent
    h=hashlib.sha256()
    for p in sorted(root.rglob('*.py')):
        h.update(str(p.relative_to(root)).encode());h.update(p.read_bytes())
    return h.hexdigest()

def connection(db):
    c=sqlite3.connect(db.directory/'sessions.sqlite3')
    c.execute('CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,created TEXT,label TEXT,payload TEXT)')
    return c

def save(db,body):
    if any(p.clock<body.request.start or p.clock>body.request.clock or p.clock%60 for p in body.predictions):raise ValueError('Prediction clock outside session')
    if body.parent_id:
        parent=read(db,body.parent_id)
        if parent.get('mode','practice')!='practice':raise ValueError('Blind checkpoints cannot branch')
        if body.request.dataset_id!=parent['request']['dataset_id']:raise ValueError('Branch dataset differs')
    account=account_replay(db,body.request)
    known={o['id'] for o in account['orders']}
    if any(n.order_id not in known for n in body.notes):raise ValueError('Journal note refers to an unknown order')
    replay=replay_state(db,ReplayRequest(dataset_id=body.request.dataset_id,clock=body.request.clock))
    value=dict(id=uuid.uuid4().hex,created=datetime.now(timezone.utc).isoformat(),label=body.label,
        storage_version=1,execution_version=VERSION,contract_version=SCHEMA_VERSION,calculation_version=calculation_version(),
        mode=body.mode,parent_id=body.parent_id,predictions=[p.model_dump() for p in body.predictions],request=body.request.model_dump(),notes=[n.model_dump() for n in body.notes],account=account,replay=replay)
    with connection(db) as c:c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(value['id'],value['created'],value['label'],json.dumps(value,allow_nan=False)))
    return value

def read(db,sid,validate=True):
    with connection(db) as c:row=c.execute('SELECT payload FROM sessions WHERE id=?',(sid,)).fetchone()
    if not row:raise HTTPException(404,'Saved session not found')
    value=json.loads(row[0])
    if validate:
        if value['storage_version']!=1 or value['execution_version']!=VERSION or value['calculation_version']!=calculation_version():raise HTTPException(409,'Saved session calculation version is incompatible; export remains available for review')
        request=AccountReplayRequest.model_validate(value['request'])
        if account_replay(db,request)!=value['account'] or replay_state(db,ReplayRequest(dataset_id=request.dataset_id,clock=request.clock))!=value['replay']:raise HTTPException(409,'Saved evidence differs from current replay; session was not changed')
    return value

@router.post('')
def create(body:Save,db=Depends(store)):return checked(save,db,body)
@router.get('')
def listing(db=Depends(store)):
    with connection(db) as c:rows=c.execute('SELECT id,created,label FROM sessions ORDER BY created DESC LIMIT 100').fetchall()
    return [dict(id=r[0],created=r[1],label=r[2]) for r in rows]
@router.get('/{sid}')
def restore(sid:str,db=Depends(store)):return checked(read,db,sid)
@router.get('/{sid}/export')
def export(sid:str,db=Depends(store)):
    from fastapi.responses import JSONResponse
    value=checked(read,db,sid,False)
    return JSONResponse(value,headers={'Content-Disposition':'attachment; filename="practice-session.json"'})


class Branch(Contract):
    clock:int=Field(strict=True,ge=0)

@router.post('/{sid}/branch')
def branch(sid:str,body:Branch,db=Depends(store)):
    parent=checked(read,db,sid)
    if parent.get('mode','practice')!='practice':raise HTTPException(409,'Blind sessions cannot rewind or branch')
    r=parent['request']
    if not r['start']<=body.clock<=r['clock']:raise HTTPException(422,'Branch clock outside saved history')
    request=AccountReplayRequest.model_validate({**r,'clock':body.clock,'commands':[c for c in r['commands'] if c['time']<=body.clock]})
    ids={c.order_id for c in request.commands}
    return checked(save,db,Save(label=parent['label']+' branch',parent_id=sid,request=request,
        notes=[n for n in parent['notes'] if n['order_id'] in ids],predictions=[p for p in parent.get('predictions',[]) if p['clock']<=body.clock]))

@router.get('/{sid}/review')
def review(sid:str,db=Depends(store)):
    from .training import summary
    value=checked(read,db,sid,False)
    return {**value,'summary':summary(value['account']),'read_only':True}
