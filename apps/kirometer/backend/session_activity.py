"""Aggregate-only adapter to Crew's local CLI session statistics (no transcripts sent)."""
import asyncio

POLL_SECONDS = 120
PERIODS = ('today', 'this_week', 'this_month')
FIELDS = ('sessions', 'messages', 'tool_calls')


def normalize(raw):
    if not isinstance(raw, dict) or not raw or raw.get('error'):
        return {'available': False, 'stale': True}
    result = {'available': True, 'stale': False,
              'incomplete': bool(raw.get('refused_transcripts', 0)),
              'source': 'kiro_cli_local_sessions'}
    for period in PERIODS:
        values = raw.get(period)
        if not isinstance(values, dict):
            return {'available': False, 'stale': True}
        result[period] = {}
        for field in FIELDS:
            n = values.get(field)
            if not isinstance(n, int) or isinstance(n, bool) or not 0 <= n <= 2147483647:
                return {'available': False, 'stale': True}
            result[period][field] = n
    return result


async def read():
    # Internal, version-bound adapter. Crew does the file scan off its event loop
    # and caches it for 120 seconds. An incompatible host degrades to unavailable.
    try:
        from kiro_crew.dashboard.handlers.usage import _cached_parse_sessions
        return normalize(await _cached_parse_sessions())
    except asyncio.CancelledError:
        raise
    except Exception:
        return {'available': False, 'stale': True}
