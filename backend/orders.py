"""Deterministic entry-only paper execution; no broker calls or wall-clock state."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from pydantic import Field
from .contracts import Contract, Timestamp, INSTRUMENTS

VERSION = 'p11-orders-v1'

class OrderCommand(Contract):
    command_id: str = Field(min_length=1, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')
    time: Timestamp
    action: Literal['submit', 'cancel']
    order_id: str = Field(min_length=1, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')
    side: Literal['buy', 'sell'] | None = None
    kind: Literal['market', 'limit', 'stop'] | None = None
    units: int | None = Field(default=None, strict=True)
    price: float | None = Field(default=None, allow_inf_nan=False)

class OrderReplayRequest(Contract):
    dataset_id: str = Field(pattern=r'^[a-f0-9]{64}$')
    start: Timestamp
    clock: Timestamp
    # Required acknowledgement: dataset metadata does not prove bid/ask basis.
    input_price_basis: Literal['bid']
    spread_pips: float = Field(default=1.0, ge=0, le=100, allow_inf_nan=False)
    commands: list[OrderCommand] = Field(default_factory=list, max_length=200)


def execute(rows, symbol, start, clock, commands, spread_pips=1.0):
    """Replay validated dataset rows; process bar closes before commands at that close.

    Fill knowledge is recorded at minute close. Market/gap prices use that minute's
    open; intrabar trigger times are deliberately unknown. Positions are separate
    entry lots (hedging), not a netted or funded account.
    """
    instrument = INSTRUMENTS[symbol]
    tick = instrument.tick_size
    spread = Decimal(str(spread_pips)) * instrument.pip_size
    if not spread.is_finite() or spread < 0 or spread > 100 * instrument.pip_size or spread % tick:
        raise ValueError('Spread must be 0–100 pips and a whole number of instrument ticks')
    if start % 60 or clock % 60 or start > clock:
        raise ValueError('Start/clock must be ordered UTC minute boundaries')
    if len({c.command_id for c in commands}) != len(commands):
        raise ValueError('Command IDs must be unique')
    if any(c.time % 60 or not start <= c.time <= clock for c in commands):
        raise ValueError('Commands must be minute-aligned within start/clock')
    if any(a.time > b.time for a, b in zip(commands, commands[1:])):
        raise ValueError('Commands must be chronological; list order breaks equal-time ties')

    def price(value):
        return Decimal(str(value)).quantize(tick, rounding=ROUND_HALF_UP)

    def text(value):
        return format(value, f'.{instrument.price_precision}f')

    orders = {}; positions = []; events = []; pending = {}; cursor = 0

    def event(kind, time, order_id, **details):
        events.append(dict(sequence=len(events)+1, type=kind, time=time, order_id=order_id, **details))

    def command(c):
        if c.action == 'cancel':
            reason = None
            if any(v is not None for v in (c.side, c.kind, c.units, c.price)):
                reason = 'Cancellation must not include order fields'
            elif c.order_id not in pending:
                reason = 'Order is unknown or no longer pending'
            if reason:
                event('cancel_rejected', c.time, c.order_id, command_id=c.command_id, reason=reason)
            else:
                pending.pop(c.order_id)['status'] = 'cancelled'
                event('cancelled', c.time, c.order_id, command_id=c.command_id)
            return
        event('submitted', c.time, c.order_id, command_id=c.command_id)
        reason = None; trigger = None
        if c.order_id in orders:
            reason = 'Order ID has already been used'
        elif c.side is None or c.kind is None:
            reason = 'Side and kind are required'
        elif c.units is None or not 1 <= c.units <= 100_000_000:
            reason = 'Units must be an integer from 1 through 100000000 base units'
        elif c.kind == 'market' and c.price is not None:
            reason = 'Market orders must not specify a trigger price'
        elif c.kind != 'market' and (c.price is None or not 0 < c.price <= 1_000_000):
            reason = 'Limit/stop price must be positive and at most 1000000'
        elif c.price is not None:
            trigger = price(c.price)
            if trigger <= 0:
                reason = 'Price rounds to zero at instrument precision'
        if reason:
            if c.order_id not in orders:
                orders[c.order_id] = dict(id=c.order_id, status='rejected', reason=reason)
            event('rejected', c.time, c.order_id, command_id=c.command_id, reason=reason)
            return
        order = dict(id=c.order_id, side=c.side, kind=c.kind, units=c.units,
                     price=text(trigger) if trigger is not None else None,
                     submitted_at=c.time, status='pending')
        orders[c.order_id] = order; pending[c.order_id] = order
        event('accepted', c.time, c.order_id, command_id=c.command_id, price=order['price'])

    for bar in rows:
        opened = bar['time']; closed = opened + 60
        if opened < start or closed > clock:
            continue
        # Commands before this close are known before this bar opens because
        # all commands are minute-aligned. Same-close commands occur afterwards.
        while cursor < len(commands) and commands[cursor].time < closed:
            command(commands[cursor]); cursor += 1
        for oid, order in list(pending.items()):
            if opened < order['submitted_at']:
                continue
            offset = spread if order['side'] == 'buy' else Decimal(0)
            quotes = [price(bar[k]) for k in ('open', 'high', 'low')]
            if min(quotes) <= 0:
                raise ValueError('Dataset quote rounds to zero at instrument precision')
            o, h, l = (q + offset for q in quotes)
            fill = None; basis = 'open'
            if order['kind'] == 'market':
                fill = o
            else:
                trigger = Decimal(order['price']); buy = order['side'] == 'buy'
                below = (order['kind'] == 'limit') == buy
                if (o <= trigger if below else o >= trigger):
                    fill = o
                elif (l <= trigger if below else h >= trigger):
                    fill = trigger; basis = 'intrabar_trigger'
            if fill is None:
                continue
            order.update(status='filled', filled_at=closed, fill_price=text(fill))
            pending.pop(oid)
            position = dict(id=f'position-{oid}', order_id=oid, symbol=symbol,
                            side=order['side'], units=order['units'], entry_price=text(fill),
                            opened_at=closed, bar_open_time=opened, status='open')
            positions.append(position)
            event('filled', closed, oid, position_id=position['id'], price=text(fill),
                  units=order['units'], bar_open_time=opened, price_basis=basis,
                  intrabar_time_unknown=basis == 'intrabar_trigger')
    while cursor < len(commands):
        command(commands[cursor]); cursor += 1
    return dict(version=VERSION, symbol=symbol, start=start, clock=clock,
                quote_model=dict(input='bid', buy='bid plus fixed simulated spread', sell='bid',
                                 spread_price=text(spread), rounding='nearest tick; half up'),
                position_model='independent entry lots; no netting, exits or account balance',
                orders=list(orders.values()), positions=positions, events=events)
