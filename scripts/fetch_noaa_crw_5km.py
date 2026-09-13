"""Fetch NOAA Coral Reef Watch 5 km daily heat-stress series for each surveyed island.

Source: NOAA CRW "Operational Daily Near-Real-Time Global 5-km Satellite Coral Bleaching
Monitoring Products" (v3.1), served by the PacIOOS ERDDAP mirror (dataset `dhw_5km`;
NOAA CoastWatch's `NOAA_DHW` redirects there).

For each island:
  1. pick the nearest sea pixel to the island's survey coordinates (the grid masks land),
  2. download CRW_DHW, CRW_BAA_7D_MAX and CRW_SSTANOMALY at that pixel, every 7th day
     from 2010-01-01 to the latest date. DHW is a rolling 12-week sum and BAA_7D_MAX is the
     max over the previous 7 days, so a weekly sample keeps annual peaks and alert-level weeks.

Outputs (data/raw/noaa_crw_5km/):
  pixels.csv                chosen pixel and distance per island
  islands/<island>.csv      raw weekly series per island (resumable: existing files are skipped)
  crw_5km_weekly.csv        all islands combined

Run from the project root:  python scripts/fetch_noaa_crw_5km.py
"""
import io
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

import certifi
import numpy as np
import pandas as pd

SERVER = 'https://pae-paha.pacioos.hawaii.edu/erddap/griddap/dhw_5km.csv'
VARIABLES = ['CRW_DHW', 'CRW_BAA_7D_MAX', 'CRW_SSTANOMALY']
START = '2010-01-01T12:00:00Z'
STRIDE_DAYS = 7
PROBE_DATE = '2024-06-01T12:00:00Z'
SEARCH_RADII_DEG = [0.1, 0.25]

DATASET = Path('master_reef_tourism_dataset.csv')
OUT_DIR = Path('data/raw/noaa_crw_5km')
CTX = ssl.create_default_context(cafile=certifi.where())


def fetch(query, retries=4):
    for attempt in range(retries):
        try:
            raw = urllib.request.urlopen(f'{SERVER}?{query}', timeout=900, context=CTX).read()
            return pd.read_csv(io.BytesIO(raw), skiprows=[1])   # row 2 holds units
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = 30 * (attempt + 1)
            print(f'    request failed ({e}); retrying in {wait}s', flush=True)
            time.sleep(wait)


def km(lat1, lon1, lat2, lon2):
    la1, lo1, la2, lo2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def nearest_sea_pixel(lat, lon):
    for r in SEARCH_RADII_DEG:
        box = fetch(f'CRW_DHW[({PROBE_DATE})][({lat + r:.4f}):({lat - r:.4f})][({lon - r:.4f}):({lon + r:.4f})]')
        box['dist_km'] = km(lat, lon, box['latitude'], box['longitude'])
        sea = box.dropna(subset=['CRW_DHW'])
        if len(sea):
            best = sea.loc[sea['dist_km'].idxmin()]
            on_land = pd.isna(box.loc[box['dist_km'].idxmin(), 'CRW_DHW'])
            return best['latitude'], best['longitude'], best['dist_km'], on_land
    raise RuntimeError(f'no sea pixel within {SEARCH_RADII_DEG[-1]} deg of ({lat}, {lon})')


def slug(name):
    return re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_')


def main():
    (OUT_DIR / 'islands').mkdir(parents=True, exist_ok=True)
    islands = (pd.read_csv(DATASET).groupby('island')
               .agg(state=('state', 'first'), latitude=('latitude', 'first'), longitude=('longitude', 'first')))

    pixels_path = OUT_DIR / 'pixels.csv'
    if pixels_path.exists():
        pixels = pd.read_csv(pixels_path, index_col='island')
    else:
        rows = []
        for name, r in islands.iterrows():
            plat, plon, dist, on_land = nearest_sea_pixel(r['latitude'], r['longitude'])
            rows.append({'island': name, 'state': r['state'], 'latitude': r['latitude'], 'longitude': r['longitude'],
                         'pixel_lat': plat, 'pixel_lon': plon, 'pixel_dist_km': round(dist, 2),
                         'coords_on_land': on_land})
            print(f'pixel  {name:28s} {dist:5.1f} km{"  (coords on land)" if on_land else ""}', flush=True)
            time.sleep(1)
        pixels = pd.DataFrame(rows).set_index('island')
        pixels.to_csv(pixels_path)

    for i, (name, p) in enumerate(pixels.iterrows(), 1):
        path = OUT_DIR / 'islands' / f'{slug(name)}.csv'
        if path.exists():
            continue
        t0 = time.time()
        query = ','.join(f'{v}[({START}):{STRIDE_DAYS}:(last)][({p["pixel_lat"]:.4f})][({p["pixel_lon"]:.4f})]'
                         for v in VARIABLES)
        series = fetch(query)
        series.insert(0, 'island', name)
        series.to_csv(path, index=False)
        print(f'series [{i:2d}/{len(pixels)}] {name:28s} {len(series)} rows, '
              f'{series["time"].iloc[0][:10]} to {series["time"].iloc[-1][:10]}, {time.time() - t0:.0f}s', flush=True)
        time.sleep(1)

    combined = pd.concat([pd.read_csv(OUT_DIR / 'islands' / f'{slug(n)}.csv') for n in pixels.index],
                         ignore_index=True)
    combined = combined.rename(columns={'time': 'date', 'CRW_DHW': 'dhw', 'CRW_BAA_7D_MAX': 'baa_7d_max',
                                        'CRW_SSTANOMALY': 'ssta', 'latitude': 'pixel_lat', 'longitude': 'pixel_lon'})
    combined['date'] = combined['date'].str[:10]
    combined.to_csv(OUT_DIR / 'crw_5km_weekly.csv', index=False)
    print(f'\nsaved {OUT_DIR / "crw_5km_weekly.csv"}: {len(combined)} rows, {combined["island"].nunique()} islands, '
          f'missing dhw {combined["dhw"].isna().sum()}', flush=True)


if __name__ == '__main__':
    sys.exit(main())
