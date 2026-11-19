"""Download Dukascopy EUR/USD BID candles in yearly batches and import them as saved datasets.

Minute data is imported in half-year datasets (Jan-Jun, Jul-Dec) because a full year is
~370,000 rows and the dataset limit is 250,000. Hourly data is downloaded by year and imported
as ONE combined dataset covering every downloaded year, so daily/weekly bias has enough history.

Examples (run from the project folder):
  .venv/bin/python scripts/fetch_dukascopy.py --granularity minute --year 2022            # both halves
  .venv/bin/python scripts/fetch_dukascopy.py --granularity minute --year 2022 --half 1   # Jan-Jun only
  .venv/bin/python scripts/fetch_dukascopy.py --granularity hour --year 2021 2022 2023
  .venv/bin/python scripts/fetch_dukascopy.py --status
Add --download-only to fetch now and import later.

Every response is cached under <data dir>/dukascopy/raw before anything is imported, so an
interrupted run resumes where it stopped. Imports are idempotent: an identical dataset is never
stored twice. Missing candles stay missing; nothing is interpolated or forward-filled. Candles
outside the fx-ny-17-v1 session calendar are dropped and the count is printed and recorded.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.calendars import is_open  # noqa: E402
from backend.datasets import MAX_ROWS, DatasetStore  # noqa: E402
from scripts.accept_real_history import decode  # noqa: E402

BASE_URL = 'https://jetta.dukascopy.com/v1/candles'
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://widgets.dukascopy.com/en/historical-data-export'}
CALENDAR = 'fx-ny-17-v1'
FIRST_YEAR = 2003
MONTH = [calendar.month_abbr[m] for m in range(13)]
SPEC = {
    'minute': {'shift': 60000, 'timeframe': '1m', 'code': 'M1'},
    'hour': {'shift': 3600000, 'timeframe': '1h', 'code': 'H1'},
}


def data_dir() -> Path:
    # Same location the app reads (backend/dataset_api.py).
    return Path(os.environ.get('CONFLUENCE_DATA_DIR', str(ROOT / '.data')))


def last_complete_day() -> date:
    """Last day of the most recent fully finished month (UTC)."""
    return date.today().replace(day=1) - timedelta(days=1)


def half_range(year: int, half: int) -> tuple[date, date] | None:
    start = date(year, 1 if half == 1 else 7, 1)
    end = min(date(year, 6, 30) if half == 1 else date(year, 12, 31), last_complete_day())
    return (start, end) if start <= end else None


def label(granularity: str, start: date, end: date) -> str:
    span = f'{start.year} {MONTH[start.month]}–{MONTH[end.month]}' if start.year == end.year else \
        f'{start.year} {MONTH[start.month]} – {end.year} {MONTH[end.month]}'
    return f'Dukascopy EUR/USD BID {SPEC[granularity]["code"]} · {span}'


# --- download -------------------------------------------------------------------------------

def minute_units(start: date, end: date) -> list[date]:
    days, d = [], start
    while d <= end:
        if d.weekday() != 5:  # Saturday is always closed; Sunday evening opens the week
            days.append(d)
        d += timedelta(days=1)
    return days


def hour_units(year: int) -> list[tuple[int, int]]:
    last = last_complete_day()
    return [(year, m) for m in range(1, 13) if date(year, m, 1) <= last]


def url_and_path(granularity: str, unit) -> tuple[str, Path]:
    raw = data_dir() / 'dukascopy' / 'raw' / granularity
    if granularity == 'minute':
        return (f'{BASE_URL}/minute/EUR-USD/BID/{unit.year}/{unit.month}/{unit.day}',
                raw / f'{unit:%Y}' / f'{unit:%Y-%m-%d}.json')
    year, month = unit
    return f'{BASE_URL}/hour/EUR-USD/BID/{year}/{month}', raw / f'{year}' / f'{year}-{month:02d}.json'


def unit_bounds(granularity: str, unit) -> tuple[int, int]:
    if granularity == 'minute':
        first = datetime(unit.year, unit.month, unit.day, tzinfo=timezone.utc)
        return int(first.timestamp()), int((first + timedelta(days=1)).timestamp())
    year, month = unit
    first = datetime(year, month, 1, tzinfo=timezone.utc)
    nxt = datetime(year + month // 12, month % 12 + 1, 1, tzinfo=timezone.utc)
    return int(first.timestamp()), int(nxt.timestamp())


def decode_unit(granularity: str, unit, raw: bytes) -> list[dict]:
    rows = decode(json.loads(raw), SPEC[granularity]['shift'], allow_empty=True)
    lo, hi = unit_bounds(granularity, unit)
    if any(not lo <= r['time'] < hi for r in rows):
        raise ValueError(f'response for {unit} contains candles outside that period')
    return rows


def fetch(url: str, attempts: int = 5) -> bytes:
    wait = 2
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt == attempts:
                raise RuntimeError(f'{url} failed after {attempts} attempts: {exc}') from exc
            print(f'    retry {attempt}/{attempts - 1} in {wait}s ({exc})', flush=True)
            time.sleep(wait)
            wait *= 2
    raise AssertionError('unreachable')


def download(granularity: str, units: list, delay: float) -> None:
    todo = [u for u in units if not url_and_path(granularity, u)[1].exists()]
    print(f'  {len(units) - len(todo)}/{len(units)} already downloaded, {len(todo)} to fetch', flush=True)
    for i, unit in enumerate(todo, 1):
        url, path = url_and_path(granularity, unit)
        raw = fetch(url)
        rows = decode_unit(granularity, unit, raw)  # validate before caching
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.part')
        tmp.write_bytes(raw)
        tmp.replace(path)
        print(f'  {granularity} {path.stem}  {len(rows):>5} candles  ({i}/{len(todo)})', flush=True)
        time.sleep(delay)


# --- import ---------------------------------------------------------------------------------

def existing_labels(store: DatasetStore) -> set[str]:
    labels, offset = set(), 0
    while page := store.list(symbol='EUR/USD', limit=100, offset=offset):
        labels |= {m['source_label'] for m in page}
        offset += 100
    return labels


def import_units(store: DatasetStore, granularity: str, units: list, name: str, slug: str) -> None:
    rows, sources, dropped = [], [], 0
    for unit in units:
        url, path = url_and_path(granularity, unit)
        raw = path.read_bytes()
        decoded = decode_unit(granularity, unit, raw)
        kept = [r for r in decoded if is_open(r['time'], CALENDAR)]
        dropped += len(decoded) - len(kept)
        rows.extend(kept)
        sources.append({'url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'rows': len(decoded)})
    if len(rows) > MAX_ROWS:
        raise ValueError(f'{name}: {len(rows):,} rows exceeds the {MAX_ROWS:,}-row dataset limit')
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=['time', 'open', 'high', 'low', 'close'], lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    content = buf.getvalue().encode()
    folder = data_dir() / 'dukascopy' / 'imports'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f'{slug}.csv').write_bytes(content)
    meta = store.import_csv(content, symbol='EUR/USD', base_timeframe=SPEC[granularity]['timeframe'],
                            calendar=CALENDAR, input_timezone='UTC', timestamp_unit='seconds',
                            volume_type='unknown', source_label=name)
    (folder / f'{slug}.json').write_text(json.dumps({
        'source': 'Dukascopy public historical endpoint', 'price_side': 'bid', 'dataset': meta,
        'csv_sha256': hashlib.sha256(content).hexdigest(), 'out_of_session_dropped': dropped,
        'normalization': 'Observed candles only; no interpolation or gap filling; volume omitted.',
        'sources': sources,
    }, indent=2) + '\n')
    q = meta['quality']
    missing = q.get('missing_bars', q.get('missing_slots', '?'))
    print(f'  imported "{name}": {meta["count"]:,} candles, missing scheduled bars: {missing}, '
          f'out-of-session dropped: {dropped}', flush=True)


# --- jobs -----------------------------------------------------------------------------------

def run_minute(store: DatasetStore, year: int, halves: list[int], download_only: bool, delay: float) -> None:
    done = existing_labels(store)
    for half in halves:
        span = half_range(year, half)
        if span is None:
            print(f'\n{year} half {half}: not finished yet (last complete month ends {last_complete_day()}), skipped')
            continue
        name = label('minute', *span)
        print(f'\n{name}  ({span[0]} → {span[1]})', flush=True)
        if name in done:
            print('  already imported, nothing to do')
            continue
        units = minute_units(*span)
        download('minute', units, delay)
        if download_only:
            print('  downloaded; import skipped (--download-only)')
        else:
            import_units(store, 'minute', units, name, f'eurusd-bid-m1-{year}-h{half}')


def run_hour(store: DatasetStore, years: list[int], download_only: bool, delay: float) -> None:
    for year in years:
        print(f'\nHourly {year}', flush=True)
        download('hour', hour_units(year), delay)
    if download_only:
        print('\nDownloaded; combined hourly import skipped (--download-only)')
        return
    cached = sorted(int(p.name) for p in (data_dir() / 'dukascopy' / 'raw' / 'hour').iterdir() if p.name.isdigit())
    gaps = [y for y in range(cached[0], cached[-1] + 1) if y not in cached]
    if gaps:
        raise SystemExit(f'Hourly years must be continuous for one combined dataset; also download: {gaps}')
    units = [u for y in cached for u in hour_units(y)]
    missing = [f'{y}-{m:02d}' for y, m in units if not url_and_path('hour', (y, m))[1].exists()]
    if missing:
        raise SystemExit(f'Hourly months not downloaded yet: {missing}. Re-run for those years.')
    start, end = date(*units[0], 1), date(units[-1][0], units[-1][1], 1)
    name = label('hour', start, end)
    print(f'\n{name}  (combined from {len(cached)} year(s))', flush=True)
    if name in existing_labels(store):
        print('  already imported, nothing to do')
        return
    import_units(store, 'hour', units, name, f'eurusd-bid-h1-{cached[0]}-{cached[-1]}')


def status(store: DatasetStore) -> None:
    raw = data_dir() / 'dukascopy' / 'raw'
    labels = existing_labels(store)
    print(f'Data folder: {data_dir()}\n\nMinute (half-year datasets):')
    years = sorted({int(p.name) for g in ('minute', 'hour') if (raw / g).exists() for p in (raw / g).iterdir() if p.name.isdigit()})
    for year in years:
        for half in (1, 2):
            span = half_range(year, half)
            if span is None:
                continue
            units = minute_units(*span)
            have = sum(url_and_path('minute', u)[1].exists() for u in units)
            if have == 0:
                continue
            name = label('minute', *span)
            print(f'  {name:<44} downloaded {have:>3}/{len(units)} days   '
                  f'{"IMPORTED" if name in labels else "not imported"}')
    print('\nHourly (downloaded months per year):')
    for year in years:
        units = hour_units(year)
        have = sum(url_and_path('hour', u)[1].exists() for u in units)
        if have:
            print(f'  {year}: {have}/{len(units)} months')
    hourly = sorted(lbl for lbl in labels if lbl.startswith('Dukascopy EUR/USD BID H1'))
    print('\nImported hourly datasets:' + ''.join(f'\n  {lbl}' for lbl in hourly) if hourly else '\nNo hourly dataset imported yet.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--granularity', choices=['minute', 'hour'])
    parser.add_argument('--year', type=int, nargs='+')
    parser.add_argument('--half', type=int, choices=[1, 2], help='minute only: 1 = Jan-Jun, 2 = Jul-Dec (default both)')
    parser.add_argument('--download-only', action='store_true')
    parser.add_argument('--delay', type=float, default=0.5, help='seconds between requests (default 0.5)')
    parser.add_argument('--status', action='store_true')
    args = parser.parse_args()
    store = DatasetStore(data_dir())
    if args.status:
        return status(store)
    if not args.granularity or not args.year:
        parser.error('give --granularity and --year, or --status')
    if any(not FIRST_YEAR <= y <= last_complete_day().year for y in args.year):
        parser.error(f'years must be between {FIRST_YEAR} and {last_complete_day().year}')
    if args.granularity == 'minute':
        for year in args.year:
            run_minute(store, year, [args.half] if args.half else [1, 2], args.download_only, args.delay)
    else:
        if args.half:
            parser.error('--half applies to minute data only')
        run_hour(store, sorted(set(args.year)), args.download_only, args.delay)
    print('\nDone. Restart ./start.sh if it was running, then pick the dataset under Saved dataset.')


if __name__ == '__main__':
    main()
