"""Training summaries computed from confirmed execution events."""
from decimal import Decimal as D

def summary(account):
    initial=D(str(account['settings']['initial_balance']))
    balance=initial;peak=initial;drawdown=D(0);net={};ambiguous=0
    for e in account['events']:
        oid=e['order_id'];delta=D(e.get('gross_pnl','0'))-D(e.get('commission','0'))
        net[oid]=net.get(oid,D(0))+delta
        balance+=delta;peak=max(peak,balance);drawdown=max(drawdown,peak-balance)
        ambiguous+=int(bool(e.get('ambiguous')) or e['type']=='ambiguous_exit_deferred')
    closed=[p for p in account['positions'] if not p['remaining_units']]
    values=[net.get(p['order_id'],D(0)) for p in closed]
    return dict(version='p15-summary-v1',closed_trades=len(closed),wins=sum(v>0 for v in values),losses=sum(v<0 for v in values),breakeven=sum(v==0 for v in values),
        net_realized_after_costs=str(balance-initial),net_equity_change=str(D(account['account']['equity'])-initial),
        max_balance_drawdown=str(drawdown),open_positions=sum(p['remaining_units']>0 for p in account['positions']),
        pending_orders=sum(o['status']=='pending' for o in account['orders']),ambiguous_events=ambiguous,
        definitions='One trade is one fully closed entry lot; partial closes grouped. Net realized includes all paid entry/exit commissions, including open lots. Drawdown samples realized balance after each confirmed ledger event, not intraminute equity.')
