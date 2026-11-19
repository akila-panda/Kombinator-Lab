"""Dataset-backed paper execution; authoritative quotes never come from clients."""
from fastapi import APIRouter, Depends
from .dataset_api import store, checked
from .datasets import DatasetStore, MAX_ROWS
from .orders import OrderReplayRequest, execute

router = APIRouter(prefix='/api/paper')


def replay(db, body):
    meta = db.get(body.dataset_id)
    if meta['base_timeframe'] != '1m':
        raise ValueError('Paper execution requires minute history')
    if not meta['start'] <= body.start <= body.clock <= meta['end']:
        raise ValueError('Requested session is outside dataset coverage')
    rows = db.range(meta['id'], body.start, None, body.clock, MAX_ROWS, 0)['candles']
    result = execute(rows, meta['symbol'], body.start, body.clock, body.commands, body.spread_pips)
    result.update(dataset_id=meta['id'], ended=body.clock == meta['end'],
                  source_label=meta['source_label'], input_price_basis_verified=False,
                  notice='Paper simulation only. Fixed spread is synthetic; no liquidity, fees, margin or tick-path model. Pending orders remain pending at data end.')
    return result


@router.post('/replay')
def paper_replay(body: OrderReplayRequest, db: DatasetStore = Depends(store)):
    return checked(replay, db, body)


from .accounting import AccountReplayRequest, execute_account


def account_replay(db, body):
    meta = db.get(body.dataset_id)
    if meta['base_timeframe'] != '1m':
        raise ValueError('Paper execution requires minute history')
    if not meta['start'] <= body.start <= body.clock <= meta['end']:
        raise ValueError('Requested session is outside dataset coverage')
    rows = db.range(meta['id'], body.start, None, body.clock, MAX_ROWS, 0)['candles']
    result = execute_account(rows, meta['symbol'], body.start, body.clock, body.commands, body.spread_pips, body.account)
    result.update(dataset_id=meta['id'], ended=body.clock == meta['end'], source_label=meta['source_label'],
                  input_price_basis_verified=False, notice='Simulated fixed spread/slippage; financing and automatic liquidation excluded. Missing periods use last observed valuation.')
    return result


@router.post('/account-replay')
def paper_account(body: AccountReplayRequest, db: DatasetStore = Depends(store)):
    return checked(account_replay, db, body)
