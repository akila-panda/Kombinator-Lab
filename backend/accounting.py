"""P12 deterministic USD paper account. No broker or wall-clock inputs."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from pydantic import Field
from .orders import OrderCommand, OrderReplayRequest, execute as entries
from .contracts import Contract, INSTRUMENTS

VERSION = 'p12-account-v1'
D = lambda value: Decimal(str(value))
CENT = Decimal('.01')


def money(value):
    return D(value).quantize(CENT, rounding=ROUND_HALF_UP)


class AccountSettings(Contract):
    initial_balance: float = Field(default=10000, gt=0, le=1_000_000_000, allow_inf_nan=False)
    leverage: int = Field(default=30, strict=True, ge=1, le=500)
    commission_per_100k: float = Field(default=3.5, ge=0, le=1000, allow_inf_nan=False)
    slippage_pips: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)


class AccountCommand(OrderCommand):
    action: Literal['submit', 'cancel', 'close']
    stop_loss: float | None = Field(default=None, gt=0, le=1_000_000, allow_inf_nan=False)
    take_profit: float | None = Field(default=None, gt=0, le=1_000_000, allow_inf_nan=False)


class AccountReplayRequest(OrderReplayRequest):
    commands: list[AccountCommand] = Field(default_factory=list, max_length=200)
    account: AccountSettings = Field(default_factory=AccountSettings)


def execute_account(rows, symbol, start, clock, commands, spread_pips=1, settings=None):
    settings = settings or AccountSettings()
    instrument = INSTRUMENTS[symbol]; tick = instrument.tick_size
    spread = D(spread_pips) * instrument.pip_size
    slip = D(settings.slippage_pips) * instrument.pip_size
    if slip % tick:
        raise ValueError('Slippage must be a whole number of instrument ticks')
    # Reuse the P11 clock, spread and command ordering validation without executing.
    validation = [OrderCommand(**c.model_dump(exclude={'stop_loss','take_profit'}, exclude_none=True))
                  if c.action != 'close' else OrderCommand(command_id=c.command_id, time=c.time, action='cancel',order_id=c.order_id)
                  for c in commands]
    entries([],symbol,start,clock,validation,spread_pips)
    initial = money(settings.initial_balance)
    if initial <= 0:
        raise ValueError('Initial balance must round to at least USD 0.01')
    balance = initial; realized = D(0); commissions = D(0)
    orders = {}; pending = {}; positions = {}; close_queue = []; events = []; cursor = 0
    mark = None; mark_time = None

    def price(value):
        return D(value).quantize(tick, rounding=ROUND_HALF_UP)

    def px(value):
        return format(value, f'.{instrument.price_precision}f')

    def emit(kind,time,oid,**detail):
        events.append(dict(sequence=len(events)+1,type=kind,time=time,order_id=oid,**detail))

    def fee(units):
        return money(D(units)*D(settings.commission_per_100k)/100000)

    def liquidation(p,bid):
        return bid if p['side']=='buy' else bid+spread

    def pnl(p,units,exit_price):
        quote=(exit_price-D(p['entry_price']))*units*(1 if p['side']=='buy' else -1)
        # EUR/USD and GBP/USD quote USD. USD/JPY converts JPY at the
        # same executable liquidation price; no unrelated future FX feed.
        return money(quote/exit_price if symbol=='USD/JPY' else quote)

    def margin(p,bid):
        notional=D(p['remaining_units']) if symbol=='USD/JPY' else D(p['remaining_units'])*bid
        return money(notional/settings.leverage)

    def account_at(bid, funding_bar=None):
        floating=D(0); used=D(0)
        for p in positions.values():
            if not p['remaining_units']:continue
            valuation=bid
            if funding_bar is not None and p['bar_open_time']==funding_bar:
                # Newly filled intrabar lots cannot fund another order with
                # a hypothetical favorable move back to this minute's open.
                valuation=D(p['entry_bid'])
            floating+=pnl(p,p['remaining_units'],liquidation(p,valuation))
            used+=margin(p,valuation)
        equity=balance+floating
        return dict(balance=balance,realized_pnl=realized,commission_paid=commissions,
                    unrealized_pnl=floating,equity=equity,used_margin=used,free_margin=equity-used)

    def close(p,units,value,time,opened,reason,ambiguous=False,command_id=None,limit=False):
        nonlocal balance,realized,commissions
        sell=p['side']=='buy'
        adjusted=value if limit else value-slip if sell else value+slip
        if adjusted<=0:raise ValueError('Slippage produces a nonpositive exit price')
        gross=pnl(p,units,adjusted);cost=fee(units)
        balance+=gross-cost;realized+=gross;commissions+=cost
        p['remaining_units']-=units
        p['realized_pnl']=str(money(D(p['realized_pnl'])+gross))
        p['status']='closed' if not p['remaining_units'] else 'open'
        if not p['remaining_units']:p['closed_at']=time
        emit('closed',time,p['order_id'],position_id=p['id'],units=units,price=px(adjusted),
             gross_pnl=str(gross),commission=str(cost),balance=str(balance),reason=reason,
             ambiguous=ambiguous,bar_open_time=opened,command_id=command_id,
             conversion_price=px(adjusted) if symbol=='USD/JPY' else None)

    def command(c):
        oid=c.order_id
        if c.action=='close':
            p=positions.get(oid)
            reason=None
            if any(v is not None for v in (c.side,c.kind,c.price,c.stop_loss,c.take_profit)):
                reason='Close accepts only target order and optional units'
            elif p is None or not p['remaining_units']:
                reason='Position is unknown or closed'
            elif c.units is not None and not 1<=c.units<=p['remaining_units']:
                reason='Close units exceed position or are not positive'
            elif any(q.order_id==oid for q in close_queue):
                reason='A close is already pending for this position'
            if reason:emit('close_rejected',c.time,oid,command_id=c.command_id,reason=reason)
            else:
                close_queue.append(c)
                emit('close_accepted',c.time,oid,command_id=c.command_id,units=c.units)
            return
        if c.action=='cancel':
            if any(v is not None for v in (c.side,c.kind,c.units,c.price,c.stop_loss,c.take_profit)) or oid not in pending:
                emit('cancel_rejected',c.time,oid,command_id=c.command_id,reason='Invalid cancellation or order no longer pending')
            else:
                pending.pop(oid)['status']='cancelled'
                emit('cancelled',c.time,oid,command_id=c.command_id)
            return
        # Reuse P11 business validation and normalized trigger prices.
        base=OrderCommand(**c.model_dump(exclude={'stop_loss','take_profit'},exclude_none=True))
        checked=entries([],symbol,start,clock,[base],spread_pips)['orders'][0]
        emit('submitted',c.time,oid,command_id=c.command_id)
        reason=checked.get('reason')
        if oid in orders:reason='Order ID has already been used'
        for v in (c.stop_loss,c.take_profit):
            if v is not None and price(v)<=0:reason='Exit price rounds to zero'
        if reason:
            if oid not in orders:orders[oid]=dict(id=oid,status='rejected',reason=reason)
            emit('rejected',c.time,oid,command_id=c.command_id,reason=reason);return
        checked.update(stop_loss=px(price(c.stop_loss)) if c.stop_loss is not None else None,
                       take_profit=px(price(c.take_profit)) if c.take_profit is not None else None)
        orders[oid]=checked;pending[oid]=checked
        emit('accepted',c.time,oid,command_id=c.command_id,price=checked['price'])

    def exit_levels(p,bid_open,bid_high,bid_low,time,opened,at_open):
        buy=p['side']=='buy';offset=D(0) if buy else spread
        o,h,l=bid_open+offset,bid_high+offset,bid_low+offset
        sl=D(p['stop_loss']) if p['stop_loss'] else None
        tp=D(p['take_profit']) if p['take_profit'] else None
        hit_sl=sl is not None and ((o<=sl if buy else o>=sl) if at_open else (l<=sl if buy else h>=sl))
        hit_tp=tp is not None and ((o>=tp if buy else o<=tp) if at_open else (h>=tp if buy else l<=tp))
        if not(hit_sl or hit_tp):return
        entry_ambiguous=p['bar_open_time']==opened and p['entry_basis']=='intrabar_trigger'
        ambiguous=not at_open and (bool(hit_sl and hit_tp) or entry_ambiguous)
        if entry_ambiguous and hit_tp and not hit_sl:
            emit('ambiguous_exit_deferred',time,p['order_id'],reason='Take-profit may precede intrabar entry',bar_open_time=opened)
            return
        stop=bool(hit_sl)
        value=o if at_open else sl if stop else tp
        close(p,p['remaining_units'],value,time,opened,'stop_loss' if stop else 'take_profit',ambiguous,limit=not stop)

    for bar in rows:
        opened=bar['time'];closed=opened+60
        if opened<start or closed>clock:continue
        while cursor<len(commands) and commands[cursor].time<closed:
            command(commands[cursor]);cursor+=1
        o,h,l,c=(price(bar[k]) for k in ('open','high','low','close'))
        if min(o,h,l,c)<=0:raise ValueError('Dataset quote rounds to zero at instrument precision')
        # Known open: existing gap exits, then queued manual closes.
        for p in positions.values():
            if p['remaining_units']:exit_levels(p,o,h,l,closed,opened,True)
        for q in close_queue:
            p=positions[q.order_id]
            if not p['remaining_units']:
                emit('close_rejected',closed,q.order_id,command_id=q.command_id,reason='Protective gap exit closed position first')
            else:close(p,q.units or p['remaining_units'],liquidation(p,o),closed,opened,'manual',command_id=q.command_id)
        close_queue=[]
        # Open candidates first. Intrabar entries cannot use proceeds of an
        # unknown-time protective exit in this same minute to fund themselves.
        candidates=[]
        for oid,order in pending.items():
            offset=spread if order['side']=='buy' else D(0)
            qo,qh,ql=o+offset,h+offset,l+offset
            value=None;basis='open'
            if order['kind']=='market':value=qo
            else:
                trigger=D(order['price']);below=(order['kind']=='limit')==(order['side']=='buy')
                if (qo<=trigger if below else qo>=trigger):value=qo
                elif (ql<=trigger if below else qh>=trigger):value=trigger;basis='intrabar_trigger'
            if value is not None:candidates.append((basis!='open',oid,value,basis))
        candidates.sort(key=lambda x:x[0]) # stable accepted order within each stage
        for _,oid,value,basis in candidates:
            order=pending.pop(oid);buy=order['side']=='buy'
            fill=value if order['kind']=='limit' else value+slip if buy else value-slip
            reason=None
            if fill<=0:reason='Slippage produces nonpositive entry price'
            sl=D(order['stop_loss']) if order['stop_loss'] else None
            tp=D(order['take_profit']) if order['take_profit'] else None
            if (sl is not None and (sl>=fill if buy else sl<=fill)) or (tp is not None and (tp<=fill if buy else tp>=fill)):
                reason='Exit levels must bracket actual entry fill; gap made bracket invalid'
            units=order['units'];cost=fee(units)
            p=dict(id='position-'+oid,order_id=oid,symbol=symbol,side=order['side'],units=units,remaining_units=units,
                   entry_price=px(fill),entry_bid=px(value-spread if buy else value),opened_at=closed,bar_open_time=opened,entry_basis=basis,status='open',
                   stop_loss=order['stop_loss'],take_profit=order['take_profit'],realized_pnl='0.00')
            if not reason:
                # Entry loss at its own executable quote includes spread and
                # slippage exactly once; commission is paid on each fill.
                bid_at_fill=value-spread if buy else value
                available=account_at(o,opened)['free_margin']
                required=margin(p,bid_at_fill)
                immediate=pnl(p,units,liquidation(p,bid_at_fill))
                if available+immediate-cost<required:reason='Insufficient free margin including entry costs'
            if reason:
                order.update(status='rejected',reason=reason)
                emit('rejected',closed,oid,reason=reason,stage='fill',bar_open_time=opened);continue
            balance-=cost;commissions+=cost
            positions[oid]=p;order.update(status='filled',filled_at=closed,fill_price=px(fill))
            emit('filled',closed,oid,position_id=p['id'],price=px(fill),units=units,commission=str(cost),
                 bar_open_time=opened,price_basis=basis,intrabar_time_unknown=basis=='intrabar_trigger')
        for p in positions.values():
            if p['remaining_units'] and p['bar_open_time']==opened and p['entry_basis']=='open':
                exit_levels(p,o,h,l,closed,opened,True)
            if p['remaining_units']:exit_levels(p,o,h,l,closed,opened,False)
        mark=c;mark_time=closed
    while cursor<len(commands):command(commands[cursor]);cursor+=1
    totals=account_at(mark) if mark is not None else dict(balance=balance,realized_pnl=realized,commission_paid=commissions,
                unrealized_pnl=D(0),equity=balance,used_margin=D(0),free_margin=balance)
    return dict(version=VERSION,symbol=symbol,start=start,clock=clock,orders=list(orders.values()),
                positions=list(positions.values()),events=events,pending_closes=[q.model_dump() for q in close_queue],
                account={k:str(money(v)) for k,v in totals.items()},mark_time=mark_time,
                margin_call=totals['free_margin']<0,settings=settings.model_dump(),
                policy=dict(currency='USD',spread_price=px(spread),slippage_price=px(slip),
                            commission='USD per 100000 base units per fill side; rounded to cents',
                            ambiguity='stop first; intrabar entry TP-only deferred',
                            financing='excluded',automatic_liquidation='excluded',
                            conversion='JPY P&L divided by executable exit/mark price; USD quotes unchanged'))
