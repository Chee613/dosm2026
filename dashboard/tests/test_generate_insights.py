"""Tests for generate_insights.py with a fake Gemini client (no API key or network needed).

Run from the project root:  python -m unittest discover -s dashboard/tests -v
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pandas as pd
from google.genai import errors
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_insights as gi  # noqa: E402
from logic import DATA_DIR, load_model_spec, score_islands  # noqa: E402
from schemas import IslandInsight  # noqa: E402


def insight(name, urgency='green', n_actions=2):
    return {'island': name, 'urgency': urgency, 'headline': 'Healthy reef, keep pressures low.',
            'why': 'Cover is good. No severe heat.', 'drivers': [{'factor': 'Cover', 'evidence': 'cover 52%'}],
            'actions': [{'action': 'Install moorings', 'actor': 'Marine park authority', 'timeframe': 'Now',
                         'rationale': 'anchor damage'},
                        {'action': 'Brief divers', 'actor': 'Tourism operators', 'timeframe': 'Ongoing',
                         'rationale': 'reduce contact'}][:n_actions],
            'monitoring': 'Check cover next survey.', 'confidence': 'medium', 'caveats': 'Forecast error ~6 pts.'}


def batch(*items):
    return json.dumps({'insights': list(items)})


OVERVIEW_JSON = json.dumps({
    'headline': 'Sabah faces record heat.', 'key_findings': ['a', 'b', 'c'],
    'top_priority_islands': [{'island': 'Tiga', 'reason': 'poor cover'}],
    'regional_patterns': [{'region': 'Sabah', 'pattern': 'heat-driven'}],
    'heat_outlook_2026': 'Severe in Sabah.', 'caveats': 'Associations only.'})


class FakeClient:
    """Returns queued responses in order; an Exception in the queue is raised instead."""

    def __init__(self, responses):
        self.responses, self.prompts = list(responses), []
        self.models = SimpleNamespace(generate_content=self._generate)

    def _generate(self, model, contents, config):
        self.prompts.append(contents)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return SimpleNamespace(text=item)


def quota_error(message):
    return errors.ClientError(429, {'error': {'code': 429, 'message': message, 'status': 'RESOURCE_EXHAUSTED'}})


class GenerateInsightsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / 'insights.json'
        base = pd.read_csv(DATA_DIR / 'islands.csv', index_col='island')
        self.scored = score_islands(base, load_model_spec())
        self.green = list(self.scored.index[self.scored['urgency'] == 'green'][:2])
        self.red = self.scored.index[self.scored['urgency'] == 'red'][0]

    def run_gen(self, client, **kw):
        kw.setdefault('path', self.tmp)
        kw.setdefault('rpm', 0)            # no rate-limit waits in tests
        kw.setdefault('log', lambda *_: None)
        return gi.generate(client=client, **kw)

    def test_valid_batch_is_saved_with_meta(self):
        client = FakeClient([batch(insight(self.green[0])), OVERVIEW_JSON])
        out = self.run_gen(client, islands=[self.green[0]])
        saved = json.loads(self.tmp.read_text(encoding='utf-8'))
        self.assertEqual(saved, out)
        rec = saved['islands'][self.green[0]]
        self.assertEqual(rec['_meta']['scenario'], '2026 to date')
        self.assertEqual(len(rec['_meta']['input_hash']), 16)
        self.assertEqual(saved['overview']['headline'], 'Sabah faces record heat.')
        self.assertIn(f'"island": "{self.green[0]}"', client.prompts[0])      # real data in the prompt
        self.assertIn('"evidence"', client.prompts[0])                         # evidence context is sent

    def test_model_cannot_change_urgency_and_extra_islands_ignored(self):
        client = FakeClient([batch(insight(self.red, urgency='green'), insight('Atlantis'))])
        out = self.run_gen(client, islands=[self.red], overview=False)
        self.assertEqual(out['islands'][self.red]['urgency'], 'red')
        self.assertNotIn('Atlantis', out['islands'])

    def test_island_missing_from_batch_is_retried_alone(self):
        a, b = self.green
        client = FakeClient([batch(insight(a)), batch(insight(b))])
        out = self.run_gen(client, islands=[a, b], overview=False, batch_size=2)
        self.assertEqual(set(out['islands']), {a, b})
        self.assertEqual(len(client.prompts), 2)
        self.assertIn(f'these 1 islands: {b}', client.prompts[1])

    def test_invalid_json_gets_one_repair_attempt(self):
        client = FakeClient([batch(insight(self.green[0], n_actions=1)), batch(insight(self.green[0]))])
        self.run_gen(client, islands=[self.green[0]], overview=False)
        self.assertEqual(len(client.prompts), 2)
        self.assertIn('did not match the schema', client.prompts[1])

    def test_still_invalid_after_repair_raises(self):
        client = FakeClient([batch(insight(self.green[0], n_actions=1))] * 2)
        with self.assertRaises(ValidationError):
            self.run_gen(client, islands=[self.green[0]], overview=False)

    def test_progress_is_saved_before_a_later_failure(self):
        a, b = self.green
        client = FakeClient([batch(insight(a)), batch(insight(b, n_actions=1)), batch(insight(b, n_actions=1))])
        with self.assertRaises(ValidationError):
            self.run_gen(client, islands=[a, b], overview=False, batch_size=1)
        saved = json.loads(self.tmp.read_text(encoding='utf-8'))
        self.assertEqual(set(saved['islands']), {a})

    def test_up_to_date_islands_are_skipped_unless_forced(self):
        a = self.green[0]
        self.run_gen(FakeClient([batch(insight(a)), OVERVIEW_JSON]), islands=[a])
        idle = FakeClient([])
        self.run_gen(idle, islands=[a])                      # nothing changed -> no requests at all
        self.assertEqual(idle.prompts, [])
        forced = FakeClient([batch(insight(a)), OVERVIEW_JSON])
        self.run_gen(forced, islands=[a], force=True)
        self.assertEqual(len(forced.prompts), 2)

    def test_merge_keeps_other_islands(self):
        self.run_gen(FakeClient([batch(insight(self.green[0]))]), islands=[self.green[0]], overview=False)
        out = self.run_gen(FakeClient([batch(insight(self.red, 'red'))]), islands=[self.red], overview=False)
        self.assertEqual(set(out['islands']), {self.green[0], self.red})

    def test_rate_limit_error_waits_as_told(self):
        client = FakeClient([quota_error('Quota exceeded. Please retry in 1.5s.'), batch(insight(self.green[0]))])
        with mock.patch.object(gi.time, 'sleep') as sleep:
            self.run_gen(client, islands=[self.green[0]], overview=False)
        sleep.assert_called_once_with(3.5)                   # 1.5 s asked + 2 s margin
        self.assertEqual(len(client.prompts), 2)

    def test_daily_quota_error_is_not_retried(self):
        client = FakeClient([quota_error('Quota exceeded for quotaId GenerateRequestsPerDayPerProjectPerModel-FreeTier')])
        with mock.patch.object(gi.time, 'sleep') as sleep, self.assertRaises(errors.ClientError):
            self.run_gen(client, islands=[self.green[0]], overview=False)
        sleep.assert_not_called()

    def test_rate_limiter_spacing(self):
        limiter = gi.RateLimiter(rpm=5)
        self.assertEqual(limiter.interval, 12.0)
        with mock.patch.object(gi.time, 'sleep') as sleep, mock.patch.object(gi.time, 'monotonic', side_effect=[100.0, 101.0, 112.0]):
            limiter.wait()
            limiter.wait()
        sleep.assert_called_once_with(11.0)

    def test_hash_changes_with_scenario(self):
        r26 = gi.island_payload(self.scored.loc[self.red], '2026 to date')
        s25 = score_islands(pd.read_csv(DATA_DIR / 'islands.csv', index_col='island'), load_model_spec(), '2025 observed')
        r25 = gi.island_payload(s25.loc[self.red], '2025 observed')
        self.assertNotEqual(gi.payload_hash(r26), gi.payload_hash(r25))

    def test_stale_island_rejected(self):
        stale = self.scored.index[self.scored['stale']][0]
        with self.assertRaises(ValueError):
            self.run_gen(FakeClient([]), islands=[stale])

    def test_env_file_loading(self):
        env = Path(tempfile.mkdtemp()) / '.env'
        env.write_text('# comment\n\nDOSM_TEST_A="quoted value"\nexport DOSM_TEST_B=plain\nDOSM_TEST_C=from_file\n',
                       encoding='utf-8')
        old = {k: os.environ.pop(k, None) for k in ['DOSM_TEST_A', 'DOSM_TEST_B', 'DOSM_TEST_C']}
        os.environ['DOSM_TEST_C'] = 'from_environment'
        try:
            gi.load_env_file(env)
            self.assertEqual(os.environ['DOSM_TEST_A'], 'quoted value')
            self.assertEqual(os.environ['DOSM_TEST_B'], 'plain')
            self.assertEqual(os.environ['DOSM_TEST_C'], 'from_environment')   # real environment wins
        finally:
            for k, v in old.items():
                os.environ.pop(k, None)
                if v is not None:
                    os.environ[k] = v

    def test_placeholder_key_is_not_a_key(self):
        saved = {k: os.environ.pop(k, None) for k in ['GOOGLE_API_KEY', 'GEMINI_API_KEY']}
        try:
            os.environ['GOOGLE_API_KEY'] = 'paste-your-key-here'
            self.assertFalse(gi.has_api_key())
            os.environ['GOOGLE_API_KEY'] = 'something-real'
            self.assertTrue(gi.has_api_key())
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None)
                if v is not None:
                    os.environ[k] = v

    def test_schema_has_no_refs(self):
        schema = json.dumps(gi.inline_refs(gi.IslandInsights.model_json_schema()))
        self.assertNotIn('$ref', schema)
        self.assertIn('Marine park authority', schema)
        IslandInsight.model_validate(insight('X'))   # fixture itself is valid


if __name__ == '__main__':
    unittest.main()
