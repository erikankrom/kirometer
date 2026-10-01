"""Crew-owned collector. No agents, OS services, credential reads or network calls."""
import asyncio
import contextlib
import datetime as dt
import math
from pathlib import Path
import sqlite3

from .usage import default_db, read_usage
from .activity import ActivityTracker

_task = None
_snapshot = None
_activity_task = None
_activity_state = None
_activity_tracker = ActivityTracker()

def bind_activity_state(state):
    global _activity_state
    if state is not None:
        _activity_state=state
        refresh_activity()


def refresh_activity():
    if _snapshot is not None:
        _snapshot.update(_activity_tracker.read(_activity_state))

async def poll_activity():
    while True:
        refresh_activity()
        await asyncio.sleep(2)


def bounded_integer(value, default, low, high):
    return value if isinstance(value, int) and not isinstance(value, bool) and low <= value <= high else default


def crew_usage(now=None):
    """Version-bound cache adapter; never invokes refresh or reads auth stores."""
    try:
        from kiro_crew.dashboard.handlers.usage import get_usage_cache
        from kiro_crew.dashboard.handlers import sessions
        cache=get_usage_cache()
        stamp=getattr(sessions,'_usage_cache_ts',0)
    except (ImportError,AttributeError,TypeError):
        return None
    return normalize_crew(cache,stamp,now)


def normalize_crew(cache,stamp,now=None):
    import time
    now=time.time() if now is None else now
    used,limit=cache.get('credits_used'),cache.get('credits_plan')
    if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 for v in (used,limit)):
        return None
    age=max(0,now-stamp) if isinstance(stamp,(int,float)) and math.isfinite(stamp) and stamp>0 else None
    return {'source':'kiro_crew_billing_cache','available':True,'observed_at':None,
            'age_seconds':round(age) if age is not None else None,
            'stale':bool(cache.get('stale')) or age is None or age>300,
            'credits':[{'used':used,'limit':limit,'remaining_plan_credits':max(0,limit-used),
                        'used_percent':used/limit*100 if limit>0 else None,'reset_at':cache.get('resets'),
                        'overage_used':max(0,used-limit)}],
            'plan':cache.get('plan') if isinstance(cache.get('plan'),str) else None,
            'activity':'unknown','error':None}


def collect(config):
    stale_after = bounded_integer(config.get('stale_after'), 300, 0, 86400)
    path = config.get('db_path') or default_db()
    try:
        result = crew_usage() if not config.get('db_path') else None
        if result is None:
            result = read_usage(Path(path), stale_after)
        result['available'] = bool(result['credits'])
        for credit in result['credits']:
            used, limit = credit['used'], credit['limit']
            valid = all(isinstance(n, (int, float)) and math.isfinite(n) for n in (used, limit))
            if not valid:
                credit.update(used=None, limit=None, remaining_plan_credits=None, used_percent=None)
            credit['overage_used'] = max(0, used - limit) if valid else None
        result['available'] = any(c['used'] is not None for c in result['credits'])
        result['error'] = None
    except (sqlite3.Error, ValueError, OSError, TypeError, OverflowError):
        result = {'source': 'kiro_local_cache', 'available': False, 'stale': True,
                  'credits': [], 'age_seconds': None, 'observed_at': None,
                  'activity': 'unknown', 'error': 'usage_cache_unavailable'}
    result.update(schema_version=1, collected_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                  activity_source=None, collector='kiro_crew_app')
    return result


async def poll(ctx):
    global _snapshot
    interval = bounded_integer(ctx.config.get('poll_seconds'), 15, 5, 300)
    while True:
        _snapshot = await asyncio.to_thread(collect, ctx.config)
        refresh_activity()
        await asyncio.sleep(interval)


async def on_startup(ctx):
    global _task, _snapshot, _activity_task
    await on_shutdown(ctx)
    _snapshot = await asyncio.to_thread(collect, ctx.config)
    _task = asyncio.create_task(poll(ctx), name='kirometer-collector')
    _activity_task = asyncio.create_task(poll_activity(), name='kirometer-activity')


async def on_shutdown(ctx):
    global _task, _snapshot, _activity_task, _activity_state, _activity_tracker
    if _activity_task:
        _activity_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _activity_task
    _activity_task=None;_activity_state=None;_activity_tracker=ActivityTracker()
    if _task:
        _task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _task
    _task = None
    _snapshot = None
    from .devices import stop
    await stop()


async def snapshot(request, ctx):
    from aiohttp import web
    bind_activity_state(request.app.get('state'))
    data = _snapshot or await asyncio.to_thread(collect, ctx.config)
    return web.json_response(data, headers={'Cache-Control': 'no-store'}, dumps=__import__('json').dumps)


async def health(request, ctx):
    from aiohttp import web
    return web.json_response({'running': bool(_task and not _task.done()),
                              'usage_available': bool(_snapshot and _snapshot['available'])})


def register_routes(ctx):
    from kiro_crew.apps.route_registry import AppRoute
    from .devices import route
    return [AppRoute('GET', '/snapshot', snapshot), AppRoute('GET', '/health', health),
            AppRoute('GET', '/devices', route),
            *[AppRoute('POST', '/devices/' + action, route) for action in ('setup','bundle','flash','status','connect','disconnect','controls','setup_bluetooth','bluetooth_scan','bluetooth_connect')]]
