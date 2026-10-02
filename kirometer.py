"""Read Kiro IDE's locally cached usage without credentials or network calls."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sqlite3
import sys
import time


def default_db(platform=None, environ=None, home=None):
    """Locate the ordinary desktop profile; --db still supports custom profiles."""
    platform = sys.platform if platform is None else platform
    environ = os.environ if environ is None else environ
    home = Path.home() if home is None else Path(home)
    if platform == 'win32':
        config = Path(environ.get('APPDATA') or home / 'AppData/Roaming')
    elif platform == 'darwin':
        config = home / 'Library/Application Support'
    else:
        config = Path(environ.get('XDG_CONFIG_HOME') or home / '.config')
    return config / 'Kiro/User/globalStorage/state.vscdb'


DEFAULT_DB = default_db()


def normalize(state, now=None, stale_after=3600):
    now = time.time() if now is None else now
    stamp = state.get('timestamp')
    age = max(0, now - stamp / 1000) if isinstance(stamp, (int, float)) else None
    credits = []
    for item in state.get('usageBreakdowns', []):
        if item.get('type') != 'CREDIT':
            continue
        used, limit = item.get('currentUsage'), item.get('usageLimit')
        valid = all(isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0 for v in (used, limit))
        credits.append({
            'used': used if valid else None,
            'limit': limit if valid else None,
            'remaining_plan_credits': max(0, limit - used) if valid else None,
            'used_percent': used / limit * 100 if valid and limit > 0 else None,
            'reset_at': item.get('resetDate'),
            # Extra credit packs have not been validated; do not invent total balance.
        })
    return {
        'source': 'kiro_local_cache',
        'observed_at': dt.datetime.fromtimestamp(stamp / 1000, dt.timezone.utc).isoformat() if age is not None else None,
        'age_seconds': round(age) if age is not None else None,
        'stale': age is None or age > stale_after,
        'credits': credits,
        'activity': 'unknown',
    }


def read_usage(path=DEFAULT_DB, stale_after=3600):
    with sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True) as db:
        row = db.execute("SELECT value FROM ItemTable WHERE key = ?", ('kiro.kiroAgent',)).fetchone()
    if row is None:
        raise ValueError('Kiro agent cache is unavailable')
    agent = json.loads(row[0])
    state = agent.get('kiro.resourceNotifications.usageState')
    if not isinstance(state, dict):
        raise ValueError('Kiro usage cache is unavailable')
    return normalize(state, stale_after=stale_after)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--stale-after', type=int, default=3600)
    args = parser.parse_args()
    if args.stale_after < 0:
        parser.error('--stale-after must be nonnegative')
    try:
        result = read_usage(args.db, args.stale_after)
    except (sqlite3.Error, ValueError, OSError):
        result = {'source': 'kiro_local_cache', 'available': False, 'stale': True, 'credits': [], 'activity': 'unknown'}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
