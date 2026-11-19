"""Versioned boundary contracts. Times are UTC Unix seconds; prices are quote/base."""
from __future__ import annotations
from decimal import Decimal
from .calendars import CalendarId, bar_bounds, is_open
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = '1.4.0'
Timeframe = Literal['1m', '5m', '15m', '1h', '4h', 'd1', 'w1']
DURATIONS = {'1m':60, '5m':300, '15m':900, '1h':3600, '4h':14400, 'd1':86400, 'w1':604800}
Symbol = Literal['EUR/USD', 'GBP/USD', 'USD/JPY']
Timestamp = Annotated[int, Field(strict=True, ge=0, le=4102444800)]
Price = Annotated[float, Field(strict=True, gt=0, allow_inf_nan=False)]
Finite = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Name = Annotated[str, Field(min_length=1, pattern=r'.*\S.*')]
Direction = Literal['bullish', 'bearish', 'neutral', 'mixed']
Availability = Literal['available', 'unavailable', 'insufficient_history']

class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)

class Instrument(Contract):
    symbol: Symbol
    base_currency: Name
    quote_currency: Name
    pip_size: Decimal = Field(gt=0, allow_inf_nan=False)
    tick_size: Decimal = Field(gt=0, allow_inf_nan=False)
    price_precision: int = Field(strict=True, ge=0, le=10)
    unit: Literal['base_currency_units'] = 'base_currency_units'
    metadata_source: Name

    @model_validator(mode='after')
    def rules(self):
        if self.symbol != f'{self.base_currency}/{self.quote_currency}':
            raise ValueError('Instrument currencies do not match symbol')
        if self.tick_size != Decimal(10) ** -self.price_precision:
            raise ValueError('Tick size must match price precision for this registry')
        if self.pip_size % self.tick_size:
            raise ValueError('Pip size must be a whole number of ticks')
        return self

INSTRUMENTS = {
    s: Instrument(symbol=s, base_currency=s[:3], quote_currency=s[-3:],
                  pip_size=Decimal('.01' if s.endswith('JPY') else '.0001'),
                  tick_size=Decimal('.001' if s.endswith('JPY') else '.00001'),
                  price_precision=3 if s.endswith('JPY') else 5,
                  metadata_source='local FX defaults; not verified broker specifications')
    for s in ['EUR/USD','GBP/USD','USD/JPY']
}

class DataSource(Contract):
    id: Name
    kind: Literal['synthetic', 'user_upload', 'provider', 'unknown']
    description: Name
    volume_type: Literal['tick_count', 'base_units', 'quote_units', 'unknown'] = 'unknown'
    provenance_verified: bool = False

LEGACY_SOURCE = DataSource(id='legacy-input', kind='unknown', description='Caller supplied candles; provenance not established')

class CanonicalCandle(Contract):
    id: Name
    symbol: Symbol
    timeframe: Timeframe
    calendar: CalendarId = 'fixed-utc-v1'
    source_id: Name
    open_time: Timestamp
    close_time: Timestamp
    observed_at: Timestamp
    state: Literal['completed', 'forming']
    open: Price
    high: Price
    low: Price
    close: Price
    volume: Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)] | None = None
    volume_type: Literal['tick_count', 'base_units', 'quote_units', 'unknown'] = 'unknown'
    quality_flags: list[Literal['synthetic', 'unverified_source', 'gap_before_unclassified', 'missing_scheduled_bars_before', 'scheduled_closure_before', 'volume_unknown']] = Field(default_factory=list)

    @model_validator(mode='after')
    def coherent(self):
        if bar_bounds(self.open_time,self.timeframe,self.calendar)!=(self.open_time,self.close_time) or not is_open(self.open_time,self.calendar):
            raise ValueError('Candle boundaries do not match its calendar/timeframe')
        if self.high < max(self.open,self.close,self.low) or self.low > min(self.open,self.close):
            raise ValueError('Invalid OHLC geometry')
        if self.observed_at < self.open_time:
            raise ValueError('Candle observed before its open')
        if self.state == 'completed' and self.observed_at < self.close_time:
            raise ValueError('Completed candle observed before close')
        if self.state == 'forming' and self.observed_at >= self.close_time:
            raise ValueError('Forming candle must be observed before scheduled close')
        if self.volume is None and self.volume_type != 'unknown':
            raise ValueError('Missing volume must have unknown units')
        return self

class MarketSnapshot(Contract):
    id: Name
    symbol: Symbol
    timeframe: Timeframe
    base_timeframe: Timeframe
    as_of: Timestamp
    input_start: Timestamp
    input_end: Timestamp
    input_count: int = Field(strict=True, gt=0)
    source: DataSource
    calendar: CalendarId = 'fixed-utc-v1'
    quality_flags: list[Name] = Field(default_factory=list)

    @model_validator(mode='after')
    def bounds(self):
        if not self.input_start < self.input_end <= self.as_of:
            raise ValueError('Snapshot input range must finish by its clock')
        if DURATIONS[self.timeframe] < DURATIONS[self.base_timeframe]:
            raise ValueError('Cannot derive a finer timeframe from coarser input')
        return self

class Evidence(Contract):
    id: Name
    symbol: Symbol
    kind: Literal['candle', 'observation', 'calculation']
    source_id: Name
    occurred_at: Timestamp
    available_at: Timestamp
    candle_id: Name | None = None
    explanation: Name

    @model_validator(mode='after')
    def timing(self):
        if self.available_at < self.occurred_at:
            raise ValueError('Evidence cannot be available before occurrence')
        if (self.kind == 'candle') != (self.candle_id is not None):
            raise ValueError('Candle evidence must reference a candle; other evidence must not')
        return self

class Finding(Contract):
    id: Name
    snapshot_id: Name
    symbol: Symbol
    timeframe: Timeframe
    module: Literal['struct', 'fxdesk', 'scalper', 'forexdashboard', 'integration']
    source_version: Name
    calculation_version: Name
    kind: Name
    title: Name
    direction: Direction | None = None
    prices: list[Price] = Field(min_length=1)
    occurred_at: Timestamp
    confirmed_at: Timestamp | None = None
    invalidated_at: Timestamp | None = None
    expired_at: Timestamp | None = None
    status: Literal['provisional', 'confirmed', 'invalidated', 'expired']
    evidence_ids: list[Name] = Field(min_length=1)
    explanation: Name
    invalidation_condition: Name
    timing_note: Name

    @model_validator(mode='after')
    def lifecycle(self):
        if self.status == 'provisional' and self.confirmed_at is not None:
            raise ValueError('Provisional finding cannot carry a confirmation')
        if self.status in ('confirmed','invalidated','expired') and self.confirmed_at is None:
            raise ValueError('Non-provisional finding needs a confirmation time')
        if self.confirmed_at is not None and self.confirmed_at < self.occurred_at:
            raise ValueError('Confirmation precedes occurrence')
        for key,status in [('invalidated_at','invalidated'),('expired_at','expired')]:
            value=getattr(self,key)
            if (value is not None) != (self.status == status):
                raise ValueError(f'{key} must match status')
            if value is not None and value < self.confirmed_at:
                raise ValueError('Lifecycle transition precedes confirmation')
        return self

class ChartPoint(Contract):
    time: Timestamp
    price: Annotated[float, Field(strict=True,ge=0,allow_inf_nan=False)]

class ZoneGeometry(Contract):
    start_time: Timestamp
    end_time: Timestamp
    top: Price
    bottom: Price

    @model_validator(mode='after')
    def bounds(self):
        if self.start_time > self.end_time or self.bottom >= self.top:
            raise ValueError('Invalid zone geometry')
        return self

class Overlay(Contract):
    pane: Literal['price','rsi'] = 'price'
    id: Name
    finding_id: Name
    kind: Literal['marker','level','line','zone']
    points: list[ChartPoint] = Field(default_factory=list)
    zone: ZoneGeometry | None = None

    @model_validator(mode='after')
    def geometry(self):
        if self.pane=='price' and any(p.price<=0 for p in self.points):raise ValueError('Price geometry must be positive')
        if self.pane=='rsi' and (self.kind!='line' or any(p.price>100 for p in self.points)):raise ValueError('RSI geometry must be a line in 0..100')
        if self.kind == 'zone':
            if self.zone is None or self.points:raise ValueError('Zone overlay requires only zone geometry')
        elif self.zone is not None or len(self.points) != (2 if self.kind == 'line' else 1):
            raise ValueError('Invalid overlay point count')
        if self.kind == 'line' and self.points[0].time >= self.points[1].time:
            raise ValueError('Line points must be chronological')
        return self

class Assessment(Contract):
    module: Literal['struct','fxdesk','scalper','forexdashboard','integration']
    kind: Name
    source_version: Name
    calculation_version: Name
    status: Availability
    direction: Direction | None = None
    metrics: dict[str, Finite] = Field(default_factory=dict)
    evidence_ids: list[Name] = Field(default_factory=list)
    explanation: Name

    @model_validator(mode='after')
    def availability(self):
        if self.status == 'available' and not self.evidence_ids:
            raise ValueError('Available assessment requires evidence')
        if self.status != 'available' and (self.metrics or self.evidence_ids or self.direction is not None):
            raise ValueError('Unavailable assessment cannot provide scores or direction')
        return self

class SentimentObservation(Contract):
    kind: Literal['position_book','order_book']
    status: Availability
    source: DataSource
    observed_at: Timestamp | None = None
    retrieved_at: Timestamp | None = None
    availability_basis: Literal['observation_time_only','retrieval_time'] = 'observation_time_only'
    score: Annotated[float, Field(strict=True, ge=-1, le=1, allow_inf_nan=False)] | None = None
    evidence_ids: list[Name] = Field(default_factory=list)
    reason: Name

    @model_validator(mode='after')
    def coherent(self):
        if self.retrieved_at is not None and (self.observed_at is None or self.retrieved_at < self.observed_at):
            raise ValueError('Retrieval cannot precede observation')
        if self.availability_basis == 'retrieval_time' and self.retrieved_at is None:
            raise ValueError('Retrieval-time availability requires retrieval time')
        if self.status == 'available' and (self.retrieved_at is None or self.availability_basis!='retrieval_time'):
            raise ValueError('Historical sentiment requires explicit retrieval availability')
        if self.status == 'available' and (self.observed_at is None or self.score is None or not self.evidence_ids):
            raise ValueError('Available sentiment requires time, score and evidence')
        if self.status != 'available' and (self.score is not None or self.evidence_ids):
            raise ValueError('Unavailable sentiment cannot contribute a score or evidence')
        return self

class SentimentResult(Contract):
    status: Availability
    observations: list[SentimentObservation] = Field(default_factory=list)
    reason: Name

    @model_validator(mode='after')
    def available(self):
        available=any(x.status == 'available' for x in self.observations)
        if available != (self.status == 'available'):
            raise ValueError('Sentiment status disagrees with its observations')
        return self

class AnalysisEnvelope(Contract):
    retrospective_findings_only: Literal[True] = True
    schema_version: Literal['1.4.0'] = SCHEMA_VERSION
    instrument: Instrument
    snapshot: MarketSnapshot
    candles: list[CanonicalCandle] = Field(min_length=1)
    evidence: list[Evidence] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    overlays: list[Overlay] = Field(default_factory=list)
    assessments: list[Assessment] = Field(default_factory=list)
    sentiment: SentimentResult

    @model_validator(mode='after')
    def references(self):
        snap=self.snapshot
        if self.instrument.symbol != snap.symbol:raise ValueError('Instrument/snapshot mismatch')
        def index(items):
            ids=[x.id for x in items]
            if len(ids) != len(set(ids)):raise ValueError('Duplicate contract IDs')
            return {x.id:x for x in items}
        candles=index(self.candles);evidence=index(self.evidence);findings=index(self.findings);index(self.overlays)
        if len(self.candles)>snap.input_count:raise ValueError('Output exceeds available base candle count')
        times=[c.open_time for c in self.candles]
        if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('Candle times must be unique and increasing')
        for c in self.candles:
            if c.symbol != snap.symbol or c.timeframe != snap.timeframe or c.source_id != snap.source.id or c.calendar != snap.calendar:
                raise ValueError('Candle context differs from snapshot')
            if (c.open_time < snap.input_start or c.open_time >= snap.input_end or c.observed_at > snap.as_of
                    or (c.state=='completed' and c.close_time>snap.input_end)
                    or (c.state=='forming' and c.observed_at>snap.input_end)):
                raise ValueError('Candle outside snapshot range')
        for e in self.evidence:
            if e.symbol != snap.symbol or e.available_at > snap.as_of:raise ValueError('Evidence mismatched or from future')
            if e.candle_id:
                if e.candle_id not in candles:raise ValueError('Missing evidence candle')
                c=candles[e.candle_id]
                if e.occurred_at != c.open_time or e.available_at < c.observed_at or e.source_id != c.source_id:
                    raise ValueError('Candle evidence disagrees with candle timing/source')
        def check_refs(refs):
            if len(refs)!=len(set(refs)) or any(r not in evidence for r in refs):raise ValueError('Missing or duplicate evidence reference')
        for f in self.findings:
            if f.snapshot_id!=snap.id or f.symbol!=snap.symbol or f.timeframe!=snap.timeframe:
                raise ValueError('Finding context differs from snapshot')
            check_refs(f.evidence_ids)
            if any(t is not None and t>snap.as_of for t in [f.occurred_at,f.confirmed_at,f.invalidated_at,f.expired_at]):
                raise ValueError('Finding lifecycle extends beyond snapshot')
            if f.confirmed_at is not None and any(evidence[r].available_at>f.confirmed_at for r in f.evidence_ids):
                raise ValueError('Finding confirmed before its evidence was available')
        for o in self.overlays:
            if o.finding_id not in findings:raise ValueError('Overlay references missing finding')
            times=[p.time for p in o.points] if o.zone is None else [o.zone.start_time,o.zone.end_time]
            if any(t>snap.as_of for t in times):raise ValueError('Overlay extends beyond snapshot')
        for a in self.assessments:check_refs(a.evidence_ids)
        for observation in self.sentiment.observations:
            check_refs(observation.evidence_ids)
            if observation.status=='available':
                time=observation.retrieved_at if observation.availability_basis=='retrieval_time' else observation.observed_at
                if time>snap.as_of:raise ValueError('Sentiment unavailable at snapshot clock')
                for ref in observation.evidence_ids:
                    e=evidence[ref]
                    if e.kind!='observation' or e.occurred_at!=observation.observed_at or e.available_at!=time or e.source_id!=observation.source.id:
                        raise ValueError('Sentiment evidence differs from its observation')
        return self
