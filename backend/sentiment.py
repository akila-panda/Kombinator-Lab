"""P06: immutable imported-book archives and a clock-bounded provider interface."""
from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from typing import Protocol
from fastapi import APIRouter, HTTPException, Query
from pydantic import Field, model_validator
from .contracts import Contract, Symbol
from .requests import BookSnapshotInput

VERSION='p06-imported-books-v1'
# Application freshness policy, not a provider publication-frequency claim.
FRESHNESS={'positionBook':86400,'orderBook':86400}

def seconds(value):return int(datetime.fromisoformat(value.replace('Z','+00:00')).timestamp())
def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

class ArchiveInput(Contract):
    label:str=Field(min_length=1,max_length=200,pattern=r'.*\S.*')
    snapshots:list[BookSnapshotInput]=Field(min_length=1,max_length=100)

    @model_validator(mode='after')
    def bounded(self):
        if sum(len(book.buckets) for s in self.snapshots for book in [s.positionBook,s.orderBook] if book)>100000:
            raise ValueError('Archive exceeds 100,000 buckets')
        return self

@dataclass(frozen=True)
class Selection:
    snapshot:dict|None
    source_id:str
    reason:str

class SentimentProvider(Protocol):
    def select(self,symbol:str,as_of:int)->Selection:...

class UnavailableProvider:
    def select(self,symbol,as_of):return Selection(None,'unconfigured-provider','No approved live source or archived observation selected; external sentiment unavailable.')

class ArchiveStore:
    def __init__(self,directory):
        path=Path(directory);path.mkdir(parents=True,exist_ok=True);self.path=path/'sentiment.sqlite3'
        with self.connect() as db:
            version=db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0,1):raise RuntimeError('Unsupported sentiment archive schema')
            db.execute('CREATE TABLE IF NOT EXISTS archives(id TEXT PRIMARY KEY,payload TEXT NOT NULL,created_at TEXT NOT NULL)')
            db.execute('PRAGMA user_version=1')
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=30)
        try:
            with db:yield db
        finally:db.close()
    def save(self,body:ArchiveInput):
        payload=body.model_dump(mode='json',exclude_none=True)
        # Reject ambiguous corrections at the same observation/retrieval coordinates.
        seen={}
        for s in payload['snapshots']:
            for kind in FRESHNESS:
                if kind not in s:continue
                b=s[kind];key=(s['instrument'],kind,b['time'],b.get('retrieved_at'))
                if key in seen and seen[key]!=b:raise ValueError('Conflicting books at identical observation/retrieval times')
                seen[key]=b
        aid=fingerprint(payload)
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO archives VALUES (?,?,?)',(aid,json.dumps(payload,sort_keys=True),datetime.now(timezone.utc).isoformat()))
        return self.metadata(aid)
    def get(self,aid):
        with self.connect() as db:row=db.execute('SELECT payload,created_at FROM archives WHERE id=?',(aid,)).fetchone()
        if row is None:raise KeyError('Sentiment archive not found')
        return json.loads(row[0]),row[1]
    def metadata(self,aid):
        body,created=self.get(aid)
        return {'id':aid,'label':body['label'],'count':len(body['snapshots']),'instruments':sorted({s['instrument'] for s in body['snapshots']}),'source_kind':'user_upload','provenance_verified':False,'created_at':created,'schema_version':1,'calculation_version':VERSION}
    def list(self,limit=100,offset=0):
        with self.connect() as db:ids=[r[0] for r in db.execute('SELECT id FROM archives ORDER BY rowid DESC LIMIT ? OFFSET ?',(limit,offset))]
        return [self.metadata(aid) for aid in ids]

class ArchiveProvider:
    def __init__(self,store:ArchiveStore,archive_id:str):self.body=store.get(archive_id)[0];self.source_id='archive:'+archive_id
    def select(self,symbol,as_of):
        instrument=symbol.replace('/','_');selected={'instrument':instrument}
        for kind,max_age in FRESHNESS.items():
            candidates=[s[kind] for s in self.body['snapshots'] if s['instrument']==instrument and kind in s
                and s[kind].get('retrieved_at') and seconds(s[kind]['retrieved_at'])<=as_of
                and 0<=as_of-seconds(s[kind]['time'])<=max_age]
            if candidates:selected[kind]=max(candidates,key=lambda b:(seconds(b['time']),seconds(b['retrieved_at'])))
        return Selection(selected if len(selected)>1 else None,self.source_id,
            'Pinned user-imported archive; source and historical retrieval times are user-asserted, not independently verified.' if len(selected)>1 else 'No matching archived book is observed, retrieved and fresh at this clock (24-hour policy); missing retrieval time is ineligible.')

def archive_store():return ArchiveStore(os.environ.get('CONFLUENCE_DATA_DIR',str(Path(__file__).resolve().parents[1]/'.data')))
router=APIRouter(prefix='/api/sentiment')
@router.get('/providers')
def providers():return {'providers':[{'id':'imported-archive','available':True,'provenance_verified':False},{'id':'live','available':False,'reason':UnavailableProvider().select('',0).reason}],'freshness_seconds':FRESHNESS,'calculation_version':VERSION}
@router.post('/archives')
def save_archive(body:ArchiveInput):
    try:return archive_store().save(body)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
@router.get('/archives')
def list_archives(limit:int=Query(100,ge=1,le=100),offset:int=Query(0,ge=0)):
    return {'archives':archive_store().list(limit,offset)}
@router.get('/archives/{archive_id}')
def archive_metadata(archive_id:str):
    try:return archive_store().metadata(archive_id)
    except KeyError as exc:raise HTTPException(404,'Sentiment archive not found') from exc
@router.get('/archives/{archive_id}/at')
def at_clock(archive_id:str,symbol:Symbol,as_of:int=Query(...,ge=0,le=4102444800)):
    from .analysis import sentiment
    import pandas as pd
    try:selected=ArchiveProvider(archive_store(),archive_id).select(symbol,as_of)
    except KeyError as exc:raise HTTPException(404,'Sentiment archive not found') from exc
    result=sentiment(selected.snapshot,symbol,pd.Timestamp(as_of,unit='s',tz='UTC'),selected.source_id)
    result['selection_reason']=selected.reason
    return result
