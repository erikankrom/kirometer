import asyncio
import copy
import unittest
from unittest.mock import patch, AsyncMock
from test_crew_app import collector
from kirometer_test_backend import session_activity


def sample():
    return {p: {'sessions': 19, 'messages': 22, 'tool_calls': 6} for p in session_activity.PERIODS}


class SessionActivityTests(unittest.IsolatedAsyncioTestCase):
    def test_aggregate_projection_excludes_unrelated_data(self):
        raw = sample()
        raw['transcript'] = 'private conversation'
        data = session_activity.normalize(raw)
        self.assertTrue(data['available'])
        self.assertNotIn('transcript', data)
        self.assertEqual(data['today']['tool_calls'], 6)

    def test_missing_and_malformed_are_not_zero_activity(self):
        for raw in ({}, None, {'error': 'unreadable'}, {'today': {}}):
            self.assertFalse(session_activity.normalize(raw)['available'])
        for value in (-1, True, 1.5, float('nan'), '19', 2147483648):
            raw = sample(); raw['today']['sessions'] = value
            self.assertFalse(session_activity.normalize(raw)['available'])
        raw = sample()
        for period in raw:
            raw[period] = dict.fromkeys(session_activity.FIELDS, 0)
        self.assertTrue(session_activity.normalize(raw)['available'])

    def test_partial_data_retains_warning(self):
        self.assertTrue(session_activity.normalize(dict(sample(), refused_transcripts=1))['incomplete'])

    async def test_session_updates_do_not_read_billing_and_survive_billing_replacement(self):
        stats = session_activity.normalize(sample())
        with patch.object(collector, '_session_stats', None), patch.object(collector, '_snapshot', {}), patch.object(collector, 'notify_update') as notify, patch.object(collector, 'collect') as billing, patch.object(session_activity, 'read', AsyncMock(return_value=stats)):
            await collector.refresh_sessions()
            notify.assert_called_once()
            billing.assert_not_called()
            collector._snapshot = {'credits': []}
            self.assertEqual(collector.current_snapshot()['session_activity']['today']['sessions'], 19)
            await collector.refresh_sessions()
            notify.assert_called_once()

    async def test_failed_refresh_retains_last_reading_as_stale(self):
        stats = session_activity.normalize(sample())
        with patch.object(collector, '_session_stats', copy.deepcopy(stats)), patch.object(collector, 'notify_update'), patch.object(session_activity, 'read', AsyncMock(return_value={'available':False,'stale':True})):
            await collector.refresh_sessions()
            self.assertTrue(collector._session_stats['stale'])
            self.assertEqual(collector._session_stats['today']['sessions'],19)

    async def test_poll_cancellation_propagates(self):
        with patch.object(collector, 'refresh_sessions', AsyncMock(side_effect=asyncio.CancelledError)):
            with self.assertRaises(asyncio.CancelledError):
                await collector.poll_sessions()
