"""Legacy UI input boundary, with explicit metadata and typed imported books."""
from datetime import datetime, timezone
from typing import Annotated, Literal
from pydantic import Field, field_validator, model_validator
from .contracts import Contract, DataSource, LEGACY_SOURCE, Price, Symbol, Timestamp, Timeframe

class CandleInput(Contract):
    time: Annotated[int, Field(strict=True, ge=0, le=4102441200)]
    open: Price
    high: Price
    low: Price
    close: Price
    volume: Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)] | None = None
    symbol: Symbol | None = None
    timeframe: Timeframe | None = None
    state: Literal['completed'] = 'completed'

    @model_validator(mode='after')
    def geometry(self):
        if self.high<max(self.open,self.close,self.low) or self.low>min(self.open,self.close):
            raise ValueError('Invalid OHLC geometry')
        if self.time%3600:raise ValueError('Analysis endpoint currently requires UTC hour-aligned candles')
        return self

    def legacy(self):
        return {'time':self.time,'open':self.open,'high':self.high,'low':self.low,'close':self.close,'volume':self.volume if self.volume is not None else 0.0}

class BookBucket(Contract):
    # OANDA export numbers are commonly strings; conversion is intentional here only.
    price: float = Field(gt=0, allow_inf_nan=False)
    shortCountPercent: float = Field(ge=0, le=100, allow_inf_nan=False)
    longCountPercent: float = Field(ge=0, le=100, allow_inf_nan=False)

    @field_validator('price','shortCountPercent','longCountPercent', mode='before')
    @classmethod
    def not_boolean(cls,value):
        if isinstance(value,bool):raise ValueError('Book numeric values cannot be booleans')
        return value

class BookInput(Contract):
    time: str
    retrieved_at: str | None = None
    price: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    bucketWidth: float | None = Field(default=None,gt=0,allow_inf_nan=False)
    buckets: list[BookBucket] = Field(min_length=1,max_length=10000)

    @field_validator('price','bucketWidth', mode='before')
    @classmethod
    def price_not_boolean(cls,value):
        if isinstance(value,bool):raise ValueError('Book price cannot be boolean')
        return value

    @field_validator('time','retrieved_at')
    @classmethod
    def utc_time(cls,value):
        if value is None:return value
        try:
            dt=datetime.fromisoformat(value.replace('Z','+00:00'))
            if dt.tzinfo is None or dt.utcoffset() is None:raise ValueError()
            seconds=dt.timestamp()
            if not 0<=seconds<=4102444800 or seconds!=int(seconds):raise ValueError()
            return dt.astimezone(timezone.utc).isoformat()
        except (ValueError,OverflowError):
            raise ValueError('Book time must have explicit timezone and whole-second precision')

    @model_validator(mode='after')
    def chronology(self):
        if self.retrieved_at and self.retrieved_at<self.time:
            raise ValueError('Book retrieval precedes observation')
        prices=[b.price for b in self.buckets]
        if len(prices)!=len(set(prices)):raise ValueError('Duplicate bucket prices')
        if any(b.longCountPercent+b.shortCountPercent>100.000001 for b in self.buckets):raise ValueError('Bucket percentages exceed 100 combined')
        if self.bucketWidth:
            ordered=sorted(prices)
            if any(b-a<self.bucketWidth*(1-1e-8) for a,b in zip(ordered,ordered[1:])):raise ValueError('Overlapping bucket intervals')
        self.buckets.sort(key=lambda b:b.price)
        return self

class BookSnapshotInput(Contract):
    instrument: Literal['EUR_USD','GBP_USD','USD_JPY']
    positionBook: BookInput | None = None
    orderBook: BookInput | None = None

    @field_validator('instrument',mode='before')
    @classmethod
    def normalize_instrument(cls,value):
        return value.strip().upper().replace('/','_') if isinstance(value,str) else value

    @model_validator(mode='after')
    def has_book(self):
        if self.positionBook is None and self.orderBook is None:raise ValueError('At least one book is required')
        return self

class AnalysisRequest(Contract):
    symbol: Symbol = 'EUR/USD'
    interval: Literal['1h','4h','d1'] = '1h'
    base_timeframe: Literal['1h'] = '1h'
    candles: list[CandleInput] = Field(min_length=60,max_length=12000)
    cutoff: int | None = Field(default=None,strict=True,ge=60,le=12000)
    snapshot: BookSnapshotInput | None = None
    archive_id:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    data_source: DataSource = Field(default_factory=lambda:LEGACY_SOURCE.model_copy())

    @model_validator(mode='after')
    def ordered(self):
        if self.snapshot and self.archive_id:raise ValueError('Choose inline snapshot or pinned archive, not both')
        if self.data_source.provenance_verified:raise ValueError('Caller cannot assert independently verified provenance')
        if self.data_source.volume_type!='unknown' and any(c.volume is None for c in self.candles):raise ValueError('Known volume units require volume on every input candle')
        times=[c.time for c in self.candles]
        if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('Candles must be strictly increasing with no duplicate times')
        if self.cutoff and self.cutoff>len(times):raise ValueError('Replay cutoff exceeds dataset length')
        if any(c.symbol is not None and c.symbol!=self.symbol for c in self.candles):raise ValueError('Candle symbol differs from request')
        if any(c.timeframe is not None and c.timeframe!=self.base_timeframe for c in self.candles):raise ValueError('Candle timeframe differs from input timeframe')
        if self.snapshot and self.snapshot.instrument!=self.symbol.replace('/','_'):raise ValueError('Book instrument differs from request')
        return self
