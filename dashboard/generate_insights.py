"""Generate LLM insights with Gemini and save them to dashboard/data/insights.json.

Usage (from the project root; needs GOOGLE_API_KEY or GEMINI_API_KEY in the environment or in a .env file
in the project root, see .env.example):
  python dashboard/generate_insights.py                          # all current islands + overview
  python dashboard/generate_insights.py --islands Redang Tioman  # just these (+ overview)
  python dashboard/generate_insights.py --scenario "2025 observed" --no-overview

Each island (and the overview) is sent as a JSON payload built from dashboard/data; Gemini returns JSON
matching schemas.py. Results are merged into insights.json, so regenerating one island keeps the rest.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logic import DATA_DIR, DEFAULT_THRESHOLDS, STATION_LABEL, load_model_spec, score_islands  # noqa: E402
from schemas import IslandInsights, Overview  # noqa: E402

INSIGHTS_PATH = DATA_DIR / 'insights.json'
DEFAULT_MODEL = 'gemini-3.1-flash-lite'
ENV_FILE = Path(__file__).resolve().parents[1] / '.env'


def load_env_file(path: Path = ENV_FILE) -> None:
    """Load KEY=VALUE lines from a .env file into os.environ; variables already set in the environment win."""
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.removeprefix('export ').split('=', 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
            value = value[1:-1]
        os.environ.setdefault(key, value)


load_env_file()

# Effect estimates from modelling.ipynb Part B (island-bootstrap 95% intervals, 338 changes, 47 islands)
EVIDENCE = {
    'model_typical_error_points': 6.05,
    'effects_on_next_change': {
        'previous-year heat stress, per 1 DHW': {'estimate': -0.38, 'ci95': [-0.59, -0.17], 'clear': True},
        'trash reported at previous survey': {'estimate': -3.0, 'ci95': [-5.5, -0.5], 'clear': True},
        'pollution indicators, per +10 pts of non-coral seabed': {'estimate': 0.0, 'ci95': [-1.69, 1.52], 'clear': False},
        'disturbance indicators, per +10 pts of non-coral seabed': {'estimate': -0.32, 'ci95': [-1.08, 0.37], 'clear': False},
    },
    'notes': ['Associations from observational survey data, not proven causes.',
              'Islands with habitual anchor damage carry about 6 points less coral cover (EDA).',
              'Crown-of-thorns outbreaks can be controlled locally by removal programmes.'],
}

SYSTEM = """You are a coral reef conservation analyst advising Malaysian marine park authorities and \
tourism operators on protecting reefs for sustainable tourism.

Rules:
- Use ONLY the facts and numbers in the JSON you are given. Never invent numbers, species, events or places.
- Every action must be concrete and practical for Malaysian marine parks, and tagged with who acts: \
"Marine park authority" or "Tourism operators". Include at least one action for each actor.
- Match actions to the evidence: severe heat -> bleaching response, reducing other stressors, monitoring; \
anchor damage -> moorings and anchoring rules; trash -> waste management; crown-of-thorns outbreaks -> removal \
programmes; losses in calm years -> local pressures are the likely lever.
- The forecast has a typical error of about 6 points, and small forecast changes on healthy reefs mostly reflect \
reefs drifting toward their regional average. Say so when evidence is weak, and set confidence accordingly.
- Describe associations, not causes. Keep the urgency level exactly as given.
- Plain, specific language. Return JSON only, matching the schema."""


def inline_refs(schema: dict) -> dict:
    """Replace $ref/$defs with inline copies (keeps the schema simple for the API)."""
    defs = schema.pop('$defs', {})

    def walk(node):
        if isinstance(node, dict):
            if '$ref' in node:
                return walk(dict(defs[node['$ref'].split('/')[-1]]))
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node
    return walk(schema)


def _round(v, nd=2):
    return None if pd.isna(v) else round(float(v), nd)


def island_payload(r: pd.Series, scenario: str) -> dict:
    return {
        'island': r.name, 'state': r['state'], 'region': r['region'], 'marine_park': r['marine_park'],
        'noaa_station': STATION_LABEL.get(r['noaa_station_id'], r['noaa_station_id']),
        'urgency': r['urgency'], 'urgency_reason': r['urgency_reason'],
        'last_survey': {'year': int(r['last_survey_year']), 'live_coral_cover_pct': _round(r['cover'], 1),
                        'change_since_previous_survey_pts': _round(r['last_change'], 1),
                        'sites_surveyed': _round(r['n_sites'], 0)},
        'forecast_next_survey': {'heat_scenario': scenario, 'heat_stress_dhw': _round(r['heat_dhw'], 1),
                                 'forecast_change_pts': _round(r['forecast_change'], 1),
                                 'projected_cover_pct': _round(r['projected_cover'], 1)},
        'heat_stress_dhw': {'2025_peak': _round(r['dhw_2025'], 1), '2026_peak_to_date': _round(r['dhw_2026'], 1)},
        'eda_site_type_2015_2025': r['site_type'],
        'local_pressures_2015_2025': {'share_of_surveys_with_anchor_damage': _round(r['anchor_share']),
                                      'share_of_surveys_with_trash': _round(r['trash_share']),
                                      'pollution_indicators_pct_of_noncoral_seabed': _round(r['pollution_share'], 1),
                                      'share_of_surveys_with_crown_of_thorns_outbreak': _round(r['cot_outbreak_share']),
                                      'boat_pressure_index_2015_2019': _round(r['boat_pressure'])},
    }


def overview_payload(scored: pd.DataFrame, scenario: str, meta: dict) -> dict:
    cur = scored[~scored['stale']]
    compact = lambda df: [{'island': i, 'state': r['state'], 'cover': _round(r['cover'], 1),
                           'forecast_change': _round(r['forecast_change'], 1), 'reason': r['urgency_reason'],
                           'site_type': r['site_type']} for i, r in df.iterrows()]
    return {
        'heat_scenario': scenario, 'noaa_data_to': meta['noaa_last_date'],
        'urgency_counts': scored['urgency'].value_counts().to_dict(),
        'red_islands': compact(cur[cur['urgency'] == 'red'].sort_values('projected_cover')),
        'yellow_islands': compact(cur[cur['urgency'] == 'yellow'].sort_values('projected_cover')),
        'green_islands': sorted(cur.index[cur['urgency'] == 'green']),
        'regions': {reg: {'islands': int(len(g)), 'mean_cover_pct': _round(g['cover'].mean(), 1),
                          'urgency': g['urgency'].value_counts().to_dict()} for reg, g in cur.groupby('region')},
        'peak_heat_stress_2026_to_date_dhw': {STATION_LABEL[s]: _round(v, 1) for s, v in
                                              cur.groupby('noaa_station_id')['dhw_2026'].first().items()},
        'eda_findings': meta['takeaways'], 'historical_change_by_prev_year_heat_band': meta['heat_band_means'],
    }


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


class RateLimiter:
    """Spaces request starts so at most `rpm` requests go out per minute (free tier: 5)."""

    def __init__(self, rpm: float):
        self.interval = 60.0 / rpm if rpm > 0 else 0.0
        self.last = None

    def wait(self):
        if self.last is not None:
            delay = self.last + self.interval - time.monotonic()
            if delay > 0:
                time.sleep(delay)
        self.last = time.monotonic()


def retry_delay(err) -> float | None:
    """Seconds the API asks us to wait (e.g. 'Please retry in 45.8s' or retryDelay '45s'), if given."""
    m = re.search(r'retry in ([\d.]+)\s*s', str(err)) or re.search(r"retryDelay'?:\s*'(\d+(?:\.\d+)?)s", str(err))
    return float(m.group(1)) if m else None


def call_gemini(client, model: str, payload: dict, schema_cls, task: str, limiter: RateLimiter, retries: int = 6):
    """One structured call: rate-limited, retries on 429/5xx (honouring the API's retry delay),
    and one repair attempt when the JSON doesn't match the schema."""
    from google.genai import errors, types
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM, temperature=0.3, response_mime_type='application/json',
        response_json_schema=inline_refs(schema_cls.model_json_schema()),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))   # no tools are used
    data = json.dumps(payload, ensure_ascii=False, default=str)
    prompt = f'{task}\n\nDATA (JSON):\n{data}'
    repaired = False
    for attempt in range(retries):
        limiter.wait()
        try:
            text = client.models.generate_content(model=model, contents=prompt, config=config).text
            return schema_cls.model_validate_json(text)
        except ValidationError as e:
            if repaired:
                raise
            repaired = True
            prompt = (f'{task}\n\nYour previous answer did not match the schema: {e.errors()[:3]}\n'
                      f'Previous answer:\n{text}\n\nReturn corrected JSON only.\n\nDATA (JSON):\n{data}')
        except errors.APIError as e:
            code = getattr(e, 'code', None)
            if code == 429 and re.search(r'per ?day', str(e), re.IGNORECASE):
                raise                                  # daily quota: waiting minutes won't help
            if not (code == 429 or isinstance(e, errors.ServerError)) or attempt == retries - 1:
                raise
            time.sleep((retry_delay(e) or 10 * 2 ** attempt) + 2)
    raise RuntimeError('Gemini call failed after retries')


def has_api_key() -> bool:
    keys = [os.environ.get('GOOGLE_API_KEY', ''), os.environ.get('GEMINI_API_KEY', '')]
    return any(k and k != 'paste-your-key-here' for k in keys)   # ignore the .env.example placeholder


def load_insights(path: Path = INSIGHTS_PATH) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {'overview': None, 'islands': {}}


def save_insights(out: dict, path: Path = INSIGHTS_PATH) -> None:
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')


def generate(scenario: str = '2026 to date', custom: dict | None = None, thresholds: dict = DEFAULT_THRESHOLDS,
             islands: list[str] | None = None, overview: bool = True, force: bool = False, client=None,
             model: str | None = None, path: Path = INSIGHTS_PATH, batch_size: int | None = None,
             rpm: float | None = None, log=print) -> dict:
    """Generate insights for `islands` (default: all current ones) and optionally the overview; merge into path.

    Islands are sent in batches (GEMINI_BATCH, default 5) to keep the request count low, requests are spaced to
    GEMINI_RPM per minute (default 5, the free-tier limit), and progress is saved after every batch. Unless
    `force`, islands and the overview whose stored input hash and model match the current data are skipped,
    so an interrupted run resumes where it stopped.
    """
    model = model or os.environ.get('GEMINI_MODEL', DEFAULT_MODEL)
    batch_size = batch_size or int(os.environ.get('GEMINI_BATCH', 5))
    limiter = RateLimiter(rpm if rpm is not None else float(os.environ.get('GEMINI_RPM', 5)))
    if client is None:
        from google import genai
        client = genai.Client()   # reads GOOGLE_API_KEY / GEMINI_API_KEY
    base = pd.read_csv(DATA_DIR / 'islands.csv', index_col='island')
    meta = json.loads((DATA_DIR / 'meta.json').read_text(encoding='utf-8'))
    scored = score_islands(base, load_model_spec(), scenario, custom, thresholds)
    current = scored[~scored['stale']]
    targets = islands if islands is not None else list(current.index)
    unknown = set(targets) - set(current.index)
    if unknown:
        raise ValueError(f'not current islands: {sorted(unknown)}')

    out = load_insights(path)
    stamp = lambda p: {'model': model, 'generated_at': datetime.now().isoformat(timespec='seconds'),
                       'scenario': scenario, 'input_hash': payload_hash(p)}
    fresh = lambda rec, p: bool(rec) and rec['_meta']['input_hash'] == payload_hash(p) and rec['_meta']['model'] == model

    payloads = {n: island_payload(current.loc[n], scenario) for n in targets}
    todo = [n for n in targets if force or not fresh(out['islands'].get(n), payloads[n])]
    if len(todo) < len(targets):
        log(f'{len(targets) - len(todo)} islands already up to date (skipped)')
    done, failed = 0, []
    for start in range(0, len(todo), batch_size):
        pending = todo[start:start + batch_size]
        for _ in range(2):                       # second pass only for islands the model left out
            res = call_gemini(client, model, {'islands': [payloads[n] for n in pending], 'evidence': EVIDENCE},
                              IslandInsights,
                              f'Write one action insight for EACH of these {len(pending)} islands: {", ".join(pending)}. '
                              'Base each insight only on that island\'s own data, and keep its urgency exactly as given.',
                              limiter)
            for ins in res.insights:
                if ins.island in pending:
                    ins.urgency = payloads[ins.island]['urgency']      # never let the model change it
                    out['islands'][ins.island] = {**ins.model_dump(), '_meta': stamp(payloads[ins.island])}
                    done += 1
                    log(f'[{done}/{len(todo)}] {ins.island}: {ins.urgency}')
            pending = [n for n in pending if not fresh(out['islands'].get(n), payloads[n])]
            save_insights(out, path)
            if not pending:
                break
        failed += pending

    if overview:
        p = overview_payload(scored, scenario, meta)
        if force or todo or not fresh(out.get('overview'), p):
            ov = call_gemini(client, model, {**p, 'evidence': EVIDENCE}, Overview,
                             'Write the Malaysia-wide overview: top priorities, regional patterns and what 2026 heat '
                             'stress means.', limiter)
            out['overview'] = {**ov.model_dump(), '_meta': stamp(p)}
            save_insights(out, path)
            log('overview: done')
    if failed:
        log(f'no insight returned for: {", ".join(failed)} (rerun to retry)')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--scenario', default='2026 to date', choices=['2026 to date', '2025 observed'])
    ap.add_argument('--islands', nargs='*', help='island names (default: all current islands)')
    ap.add_argument('--no-overview', action='store_true')
    ap.add_argument('--force', action='store_true', help='regenerate even islands that are already up to date')
    args = ap.parse_args()
    if not has_api_key():
        sys.exit('No Gemini key found: add GOOGLE_API_KEY=... to .env in the project folder (see .env.example).')
    generate(args.scenario, islands=args.islands, overview=not args.no_overview, force=args.force)
    print(f'saved {INSIGHTS_PATH}')


if __name__ == '__main__':
    main()
