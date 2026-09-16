from collections import defaultdict


def parse_noaa_row(parts):
    """Return year, SST anomaly and DHW from a NOAA CRW data row."""
    return int(parts[0]), float(parts[6]), float(parts[8])


def make_next_observation_rows(rows):
    """Attach each unit's next observed coral-change target to its prior row."""
    by_unit = defaultdict(list)
    for row in rows:
        key = row.get("site_id") or row["island"]
        by_unit[key].append(row)

    result = []
    for unit_rows in by_unit.values():
        unit_rows.sort(key=lambda row: int(row["survey_year"]))
        for current, following in zip(unit_rows, unit_rows[1:]):
            if int(following["survey_year"]) <= int(current["survey_year"]):
                continue
            target = following.get("lcc_change_rate")
            if target in (None, ""):
                continue
            result.append({
                **current,
                "target_year": int(following["survey_year"]),
                "target_lcc_change_rate": float(target),
            })
    return result


def expanding_year_splits(target_years, test_years=5):
    """Return expanding-window index splits for the latest target years."""
    years = [int(year) for year in target_years]
    test_set = sorted(set(years))[-test_years:]
    return [
        (
            [index for index, year in enumerate(years) if year < test_year],
            [index for index, year in enumerate(years) if year == test_year],
        )
        for test_year in test_set
        if any(year < test_year for year in years)
    ]


def heat_category(dhw):
    """Return the declared descriptive NOAA DHW band."""
    if dhw is None:
        return None
    if dhw < 1:
        return "DHW < 1"
    if dhw < 4:
        return "DHW 1–<4"
    return "DHW ≥ 4"
