"""Build the browser dashboard data bundle from checked pipeline outputs."""

import csv
import json
import shutil
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.economic_valuation import load_dmpm_tev
from scripts.stress_attribution import (
    FACTOR_GROUPS, FEATURE_INFO, GROUP_NOTES, STRESSOR_GROUPS,
)


PROCESSED = ROOT / "data/processed"
DASHBOARD = ROOT / "dashboard"
REPORT_FIGURES = ROOT / "reports/figures"

# Evidence-tab figures not already written to dashboard/figures by train_models.py.
EVIDENCE_FIGURES = [
    "01_tourism_data_gap.png",
    "02_national_coral_cover_trajectory.png",
    "03_satellite_thermal_stress_dhw.png",
    "04_economic_valuation_pillars.png",
    "11_all_factor_associations.png",
    "12_dataset_completeness_matrix.png",
]


def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def number(value, cast=float, default=0):
    return cast(value) if value not in (None, "") else default


# Inputs whose push rounds to 0.00 pp/yr did not move the prediction and are left out.
MIN_INPUT_PUSH_PP = 0.005


def attach_stress_evidence(priorities):
    """For each unit's top (or strongest) stressor group, list the surveyed value of each
    input, how it compares across the ranked units, and that input's push in pp/yr."""
    pushes = {row["island"]: row for row in read_csv(PROCESSED / "stress_feature_contributions.csv")}
    surveys = {(row["island"], int(row["survey_year"])): row
               for row in read_csv(PROCESSED / "master_reef_tourism_dataset.csv")}
    latest = {item["island"]: surveys[(item["island"], item["surveyYear"])] for item in priorities}
    across = {feature: [float(row[feature]) for row in latest.values() if row[feature] not in ("", None)]
              for feature in FEATURE_INFO}

    for item in priorities:
        groups = {group["name"]: group["pp"] for group in item["stress"]["groups"]}
        # Evidence follows the listed (report-primary) stressor; units without one show none.
        group = item["stress"]["topStressor"]
        push = groups[group] if group else 0.0
        if group is None:
            item["stress"]["evidence"] = None
            continue
        entries = []
        for feature in FACTOR_GROUPS[group]:
            pp = float(pushes[item["island"]][feature])
            if abs(pp) < MIN_INPUT_PUSH_PP:
                continue
            label, kind = FEATURE_INFO[feature]
            raw = latest[item["island"]][feature]
            value = float(raw) if raw not in ("", None) else None
            column = across[feature]
            entries.append({
                "label": label,
                "kind": kind,
                "value": value,
                "rank": None if value is None else 1 + sum(other > value for other in column),
                "ties": None if value is None else sum(other == value for other in column),
                "of": len(column),
                "median": statistics.median(column),
                "mentioned": sum(other >= 1 for other in column) if kind == "flag" else None,
                "pp": pp,
            })
        entries.sort(key=lambda entry: entry["pp"])
        item["stress"]["evidence"] = {
            "group": group,
            "pp": push,
            "belowThreshold": False,
            "note": GROUP_NOTES[group],
            "items": entries,
        }


def build_bundle():
    priorities = []
    for row in read_csv(PROCESSED / "reef_priority_predictions.csv"):
        priorities.append({
            "rank": int(row["priority_rank"]),
            "island": row["island"],
            "state": row["state"],
            "ecoregion": row["ecoregion"],
            "lat": float(row["latitude"]),
            "lng": float(row["longitude"]),
            "marinePark": row["marine_park"],
            "surveyYear": int(row["survey_year"]),
            "lcc": float(row["live_coral_cover_pct"]),
            "lccChangeRate": number(row["lcc_change_rate"]),
            "dhwContext": number(row["noaa_max_dhw"]),
            "predictedNextChange": float(row["predicted_next_change_pct_per_year"]),
            "predictionLower": float(row["prediction_lower"]),
            "predictionUpper": float(row["prediction_upper"]),
            "tier": row["priority_tier"],
            "sourceConfidence": row["confidence"],
            "evidence": row["evidence"],
            "nextStep": row["recommended_next_step"],
        })

    # Each unit's prediction split into factor groups (baseline + groups = prediction).
    stress = {row["island"]: row for row in read_csv(PROCESSED / "stress_contributions.csv")}
    for item in priorities:
        row = stress[item["island"]]
        item["stress"] = {
            "baseline": float(row["baseline_pp"]),
            "groups": [{"name": group, "pp": float(row[group]), "stressor": group in STRESSOR_GROUPS}
                       for group in FACTOR_GROUPS],
            "topStressor": row["top_stressor"] or None,
            "topStressorPp": float(row["top_stressor_pp"]),
            "insight": row["insight"],
        }

    attach_stress_evidence(priorities)

    island_year_groups = defaultdict(lambda: {"lccs": [], "dhws": []})
    for row in read_csv(PROCESSED / "master_reef_tourism_dataset.csv"):
        if row.get("live_coral_cover_pct") not in ("", None):
            key = (row["island"], int(row["survey_year"]))
            island_year_groups[key]["lccs"].append(float(row["live_coral_cover_pct"]))
            if row.get("noaa_max_dhw") not in ("", None):
                island_year_groups[key]["dhws"].append(float(row["noaa_max_dhw"]))

    history = defaultdict(list)
    for (island, year), vals in sorted(island_year_groups.items(), key=lambda item: (item[0][0], item[0][1])):
        mean_lcc = sum(vals["lccs"]) / len(vals["lccs"])
        mean_dhw = sum(vals["dhws"]) / len(vals["dhws"]) if vals["dhws"] else 0.0
        history[island].append({
            "year": year,
            "lcc": round(mean_lcc, 2),
            "dhwContext": round(mean_dhw, 2),
        })

    # All 90 rows match the five Department of Marine Park state datasets (2000-2017).
    visitors = defaultdict(lambda: {"domestic": 0, "foreign": 0})
    for row in read_csv(ROOT / "data/raw/structured/taman_laut_visitors_2000_2017.csv"):
        year = int(row["year"])
        visitors[year]["domestic"] += int(row["domestic_visitors"])
        visitors[year]["foreign"] += int(row["foreign_visitors"])
    visitor_trend = [
        {"year": year, **values, "total": values["domestic"] + values["foreign"]}
        for year, values in sorted(visitors.items())
    ]

    metrics = json.loads((ROOT / "output/model_evaluation_metrics.json").read_text(encoding="utf-8"))
    paired = read_csv(PROCESSED / "paired_change_summary.csv")[0]
    latest_mean = sum(item["lcc"] for item in priorities) / len(priorities)

    # 2024 bleaching: the report's own headline figures (p.4), plus the site table size.
    headline = {row["metric"]: float(row["value_pct"])
                for row in read_csv(ROOT / "data/raw/structured/reef_check/bleaching_2024_headline.csv")}
    bleaching_sites = read_csv(ROOT / "data/raw/structured/reef_check/bleaching_2024.csv")

    economics = json.loads((PROCESSED / "tourism_economics.json").read_text(encoding="utf-8"))
    park_economics = read_csv(PROCESSED / "park_economics.csv")
    for row in park_economics:
        for key in ("visitors_per_year", "spending_rm", "reef_adjacent_rm"):
            row[key] = int(row[key])

    return {
        "nationalKPIs": {
            "latestMeanCoralCover": latest_mean,
            "latestSurveyYear": max(item["surveyYear"] for item in priorities),
            "pairedChange2024To2025": float(paired["change_pp"]),
            "pairedUnits": int(paired["paired_units"]),
            "priorityCount": sum(item["tier"] == "High screening priority" for item in priorities),
            "surveyedUnits": len(priorities),
            "bleachingMortality": headline["mean_bleaching_mortality"],
            "bleachingCoralsBleached": headline["corals_bleached"],
            "bleachingTerengganuMortality": headline["terengganu_mean_mortality"],
            "bleachingSiteRecords": len(bleaching_sites),
        },
        "tourismEconomics": economics,
        "parkEconomics": park_economics,
        "priorityIslands": priorities,
        "islandHistory": dict(history),
        "factorRelationships": read_csv(PROCESSED / "factor_relationships.csv"),
        "heatSummary": read_csv(PROCESSED / "heat_category_summary.csv"),
        "modelMetrics": metrics,
        "validationByYear": read_csv(PROCESSED / "model_validation_by_year.csv"),
        "tourismDataGap": {
            "source": "Department of Marine Park Malaysia / data.gov.my (five state datasets)",
            "verifiedCoverage": "2000-2017 state marine-park totals",
            "annualTrend": visitor_trend,
            "limitation": "State marine-park totals end in 2017 and cannot be assigned to individual reefs. "
                          "Island-level arrivals are published only for 11 monitoring units in 2024 "
                          "(Sabah Parks; Terengganu State Tourism Department), so no series links visitor "
                          "exposure to reef change over time.",
        },
        "economicValuation": load_dmpm_tev(),
    }


def main():
    bundle = build_bundle()
    payload = json.dumps(bundle, indent=2, ensure_ascii=False)
    output = (
        "// Auto-generated by scripts/build_web_dashboard_data.py\n"
        f"window.REEFSAFE_DATA = {payload};\n"
        "window.TOURISM_DATA_GAP = window.REEFSAFE_DATA.tourismDataGap;\n"
        "window.ECONOMIC_VALUATION = window.REEFSAFE_DATA.economicValuation;\n"
    )
    for name in EVIDENCE_FIGURES:
        shutil.copyfile(REPORT_FIGURES / name, DASHBOARD / "figures" / name)
    target = DASHBOARD / "data.js"
    target.write_text(output, encoding="utf-8")
    print(f"Built {target} with {len(bundle['priorityIslands'])} monitoring units")


if __name__ == "__main__":
    main()
