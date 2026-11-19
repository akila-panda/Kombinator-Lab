"""Immutable SQLite datasets, bounded CSV import, and prefix/range retrieval."""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import csv
import hashlib
import io
import json
import math
import sqlite3
from .contracts import CanonicalCandle, INSTRUMENTS
from .calendars import CALENDARS, SECONDS, is_open, quality_report

MAX_ROWS=250000
MAX_BYTES=32*1024*1024
STORE_VERSION=2

class EventJournalError(RuntimeError):
    pass

def parse_time(value,input_timezone='UTC',timestamp_unit='seconds'):
    text=str(value).strip()
    try:
        numeric=float(text)
    except ValueError:numeric=None
    if numeric is not None:
        if timestamp_unit=='milliseconds':numeric/=1000
        if not math.isfinite(numeric) or numeric!=int(numeric):raise ValueError('Timestamp must be whole UTC seconds')
        return int(numeric)
    try:dt=datetime.fromisoformat(text.replace('Z','+00:00'))
    except ValueError:raise ValueError('Invalid ISO timestamp')
    if dt.tzinfo is None:
        zone=ZoneInfo(input_timezone);candidates=set()
        for fold in (0,1):
            aware=dt.replace(tzinfo=zone,fold=fold)
            if aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)==dt:candidates.add(aware.timestamp())
        if len(candidates)!=1:raise ValueError('Ambiguous/nonexistent local timestamp; supply an explicit UTC offset')
        seconds=candidates.pop()
    else:seconds=dt.timestamp()
    if seconds!=int(seconds):raise ValueError('Subsecond candle timestamps are unsupported')
    return int(seconds)

def read_csv(data,*,symbol,base_timeframe,input_timezone,calendar,timestamp_unit='seconds',volume_type='unknown'):
    if len(data)>MAX_BYTES:raise ValueError('CSV exceeds 32 MiB')
    if symbol not in INSTRUMENTS or base_timeframe not in ('1m','1h') or calendar not in CALENDARS:raise ValueError('Unsupported dataset metadata')
    if timestamp_unit not in ('seconds','milliseconds'):raise ValueError('Unsupported timestamp unit')
    try:ZoneInfo(input_timezone)
    except (ZoneInfoNotFoundError,ValueError):raise ValueError('Unknown IANA input timezone')
    try:text=data.decode('utf-8-sig')
    except UnicodeDecodeError:raise ValueError('CSV must be UTF-8')
    reader=csv.DictReader(io.StringIO(text),strict=True)
    if not reader.fieldnames:raise ValueError('Missing CSV header')
    header=[x.strip().lower() for x in reader.fieldnames]
    if len(set(header))!=len(header):raise ValueError('Duplicate CSV headers')
    required={'time','open','high','low','close'}
    allowed=required|{'volume','symbol','timeframe','state','complete'}
    if not required<=set(header) or set(header)-allowed:raise ValueError('CSV needs time,open,high,low,close; optional volume,symbol,timeframe,state,complete')
    reader.fieldnames=header;rows=[];previous=None
    for line,row in enumerate(reader,2):
        if len(rows)>=MAX_ROWS:raise ValueError('CSV exceeds 250,000 rows')
        try:
            if None in row or any(v is None for v in row.values()):raise ValueError('Wrong number of CSV fields')
            if row.get('symbol') and row['symbol'].strip().replace('_','/')!=symbol:raise ValueError('Row symbol differs from selected pair')
            if row.get('timeframe') and row['timeframe'].strip()!=base_timeframe:raise ValueError('Row timeframe differs from selected granularity')
            if row.get('state') and row['state'].strip().lower()!='completed':raise ValueError('Only completed candles may be imported')
            if row.get('complete') and row['complete'].strip().lower() not in ('true','1'):raise ValueError('Incomplete candles cannot be imported')
            t=parse_time(row['time'],input_timezone,timestamp_unit)
            if previous is not None and t<=previous:raise ValueError('Duplicate or unsorted timestamp; rows must be strictly increasing')
            if not is_open(t,calendar):raise ValueError('Candle outside selected calendar; choose the correct source calendar')
            volume=float(row['volume']) if row.get('volume','').strip() else None
            c=CanonicalCandle(id=f'import:{t}',symbol=symbol,timeframe=base_timeframe,calendar=calendar,source_id='upload',open_time=t,close_time=t+SECONDS[base_timeframe],observed_at=t+SECONDS[base_timeframe],state='completed',**{k:float(row[k]) for k in ['open','high','low','close']},volume=volume,volume_type=volume_type)
            rows.append({'time':t,'open':c.open,'high':c.high,'low':c.low,'close':c.close,'volume':c.volume});previous=t
        except (ValueError,TypeError,OverflowError) as exc:raise ValueError(f'CSV row {line}: {exc}') from exc
    if not rows:raise ValueError('CSV contains no candles')
    return rows

class DatasetStore:
    def __init__(self,directory):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.path=self.directory/'history.sqlite3'
        with self.connection() as db:
            version=db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0,1,STORE_VERSION):raise RuntimeError('Unsupported history database version; no automatic destructive migration')
            db.executescript('''CREATE TABLE IF NOT EXISTS datasets(id TEXT PRIMARY KEY, metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS candles(dataset_id TEXT NOT NULL REFERENCES datasets(id), position INTEGER NOT NULL,
                time INTEGER NOT NULL, open REAL NOT NULL, high REAL NOT NULL, low REAL NOT NULL, close REAL NOT NULL, volume REAL,
                PRIMARY KEY(dataset_id,time), UNIQUE(dataset_id,position));''')
            db.executescript('''CREATE TABLE IF NOT EXISTS finding_events(
                dataset_id TEXT NOT NULL REFERENCES datasets(id), interval TEXT NOT NULL, version TEXT NOT NULL,
                position INTEGER NOT NULL,event_id TEXT NOT NULL,available_at INTEGER NOT NULL,payload TEXT NOT NULL,
                PRIMARY KEY(dataset_id,interval,version,event_id),UNIQUE(dataset_id,interval,version,position));
                CREATE TABLE IF NOT EXISTS event_runs(dataset_id TEXT NOT NULL REFERENCES datasets(id),interval TEXT NOT NULL,
                version TEXT NOT NULL,as_of INTEGER NOT NULL,event_count INTEGER NOT NULL,fingerprint TEXT NOT NULL,
                PRIMARY KEY(dataset_id,interval,version,as_of));''')
            db.execute(f'PRAGMA user_version={STORE_VERSION}')

    @contextmanager
    def connection(self):
        db=sqlite3.connect(self.path,timeout=30);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:yield db
        finally:db.close()

    def save(self,rows,*,symbol,base_timeframe,calendar,source_kind,source_label,input_timezone='UTC',timestamp_unit='seconds',volume_type='unknown',raw_sha256=None):
        if not 0<len(rows)<=MAX_ROWS:raise ValueError('Dataset row limit exceeded')
        if source_kind not in ('synthetic','user_upload'):raise ValueError('Only synthetic or uploaded sources are supported')
        # Normalize values before hashing; exact repeat imports are idempotent, never overwritten.
        content=[{'time':r['time'],**{k:float(r[k]) for k in ['open','high','low','close']},'volume':None if r.get('volume') is None else float(r['volume'])} for r in rows]
        fingerprint=hashlib.sha256(json.dumps(content,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        identity={'content_sha256':fingerprint,'symbol':symbol,'base_timeframe':base_timeframe,'calendar':calendar,'source_kind':source_kind,'source_label':source_label,'input_timezone':input_timezone,'timestamp_unit':timestamp_unit,'volume_type':volume_type,'raw_sha256':raw_sha256}
        did=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
        metadata={'id':did,**identity,'storage_version':STORE_VERSION,'count':len(rows),'start':rows[0]['time'],'end':rows[-1]['time']+SECONDS[base_timeframe],'stored_timezone':'UTC','state':'completed','provenance_verified':False,'created_at':datetime.now(timezone.utc).isoformat(),'quality':quality_report(rows,base_timeframe,calendar)}
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT metadata FROM datasets WHERE id=?',(did,)).fetchone()
            if old:return json.loads(old[0])
            db.execute('INSERT INTO datasets VALUES (?,?)',(did,json.dumps(metadata)))
            db.executemany('INSERT INTO candles VALUES (?,?,?,?,?,?,?,?)',[(did,i,r['time'],r['open'],r['high'],r['low'],r['close'],r['volume']) for i,r in enumerate(content)])
        return metadata

    def import_csv(self,data,**metadata):
        parse={k:metadata[k] for k in ['symbol','base_timeframe','calendar','input_timezone','timestamp_unit','volume_type']}
        rows=read_csv(data,**parse)
        return self.save(rows,source_kind='user_upload',source_label=metadata['source_label'],raw_sha256=hashlib.sha256(data).hexdigest(),**parse)

    def get(self,did):
        with self.connection() as db:r=db.execute('SELECT metadata FROM datasets WHERE id=?',(did,)).fetchone()
        if r is None:raise KeyError('Dataset not found')
        return json.loads(r[0])

    def list(self,symbol=None,limit=100,offset=0):
        # Metadata is bounded to 100 returned datasets; symbol filter is evaluated in SQL JSON.
        with self.connection() as db:
            rows=db.execute('SELECT metadata FROM datasets WHERE (? IS NULL OR json_extract(metadata,\'$.symbol\')=?) ORDER BY rowid DESC LIMIT ? OFFSET ?',(symbol,symbol,limit,offset)).fetchall()
        return [json.loads(x[0]) for x in rows]

    @staticmethod
    def rows(rows):return [{k:r[k] for k in ['time','open','high','low','close','volume']} for r in rows]

    def prefix(self,did,cutoff):
        meta=self.get(did)
        if cutoff<1 or cutoff>meta['count']:raise ValueError('Cutoff exceeds dataset bounds')
        with self.connection() as db:r=db.execute('SELECT * FROM candles WHERE dataset_id=? AND position<? ORDER BY position',(did,cutoff)).fetchall()
        return meta,self.rows(r)

    def range(self,did,start,end,as_of,limit=1000,warmup=0):
        meta=self.get(did);step=SECONDS[meta['base_timeframe']]
        start=meta['start'] if start is None else start;end=meta['end'] if end is None else end;as_of=meta['end'] if as_of is None else as_of
        if start>=end:raise ValueError('Range start must precede end')
        with self.connection() as db:
            earlier=db.execute('SELECT * FROM candles WHERE dataset_id=? AND time<? AND time+?<=? ORDER BY time DESC LIMIT ?',(did,start,step,as_of,warmup)).fetchall()
            rows=db.execute('SELECT * FROM candles WHERE dataset_id=? AND time>=? AND time<? AND time+?<=? ORDER BY time LIMIT ?',(did,start,end,step,as_of,limit+1)).fetchall()
        truncated=len(rows)>limit;page=rows[:limit]
        return {'dataset_id':did,'as_of':as_of,'warmup':self.rows(list(reversed(earlier))),'warmup_requested':warmup,'warmup_returned':len(earlier),'warmup_sufficient':len(earlier)==warmup,'candles':self.rows(page),'truncated':truncated,'next_start':rows[limit]['time'] if truncated else None,'range_start':start,'range_end':end}

    def record_events(self,did,interval,version,events,as_of):
        """Append-only event journal; replay mismatch is a server integrity failure."""
        from .lifecycle import digest
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            existing={r['event_id']:r['payload'] for r in db.execute('SELECT event_id,payload FROM finding_events WHERE dataset_id=? AND interval=? AND version=?',(did,interval,version))}
            for position,event in enumerate(events):
                payload=json.dumps(event,sort_keys=True,separators=(',',':'))
                if event['id'] in existing:
                    if existing[event['id']]!=payload:raise EventJournalError('Stored event differs from deterministic replay')
                else:
                    try:db.execute('INSERT INTO finding_events VALUES (?,?,?,?,?,?,?)',(did,interval,version,position,event['id'],event['available_at'],payload))
                    except sqlite3.IntegrityError as exc:raise EventJournalError('Event position conflicts with saved history') from exc
            signature=digest(events)
            prior=db.execute('SELECT fingerprint FROM event_runs WHERE dataset_id=? AND interval=? AND version=? AND as_of=?',(did,interval,version,as_of)).fetchone()
            if prior and prior[0]!=signature:raise EventJournalError('Saved event clock differs from replay')
            db.execute('INSERT OR IGNORE INTO event_runs VALUES (?,?,?,?,?,?)',(did,interval,version,as_of,len(events),signature))

    def events(self,did,interval,version,as_of,after=-1,limit=100):
        meta=self.get(did);clock=meta['end'] if as_of is None else as_of
        with self.connection() as db:
            coverage=db.execute('SELECT MAX(as_of) FROM event_runs WHERE dataset_id=? AND interval=? AND version=?',(did,interval,version)).fetchone()[0]
            rows=db.execute('SELECT position,payload FROM finding_events WHERE dataset_id=? AND interval=? AND version=? AND available_at<=? AND position>? ORDER BY position LIMIT ?',(did,interval,version,clock,after,limit+1)).fetchall()
        return {'dataset_id':did,'interval':interval,'calculation_version':version,'as_of':clock,'status':'available' if coverage is not None and meta['start']<=clock<=coverage else 'unavailable','computed_through':min(coverage,clock) if coverage is not None else None,'events':[json.loads(r['payload']) for r in rows[:limit]],'truncated':len(rows)>limit,'next_after':rows[limit-1]['position'] if len(rows)>limit else None}
