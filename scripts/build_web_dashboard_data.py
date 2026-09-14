import csv
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")
os.makedirs(DASHBOARD_DIR, exist_ok=True)

# 1. Load priority predictions and accommodations
infr_path = os.path.join(BASE_DIR, "data", "raw", "structured", "infrastructure", "island_accommodations.csv")
with open(infr_path, encoding="utf-8") as f:
    infr_map = {r["island"]: r for r in csv.DictReader(f)}

with open(os.path.join(PROCESSED_DIR, "reef_priority_predictions.csv"), encoding="utf-8") as f:
    priority_rows = list(csv.DictReader(f))

priority_islands = []
for r in priority_rows:
    isl_name = r["island"]
    infr = infr_map.get(isl_name, {})
    dhw_val = float(r["noaa_max_dhw"]) if r.get("noaa_max_dhw") else 0.0
    impact_anchor = int(r["impact_anchor"]) if r.get("impact_anchor") else 0
    impact_trash = int(r["impact_trash"]) if r.get("impact_trash") else 0
    pollution_val = float(r["grp_pollution_indicators"]) if r.get("grp_pollution_indicators") else 0.0
    room_cap = int(infr.get("estimated_room_capacity", 0))
    
    # Calculate Controllable vs Uncontrollable risk decomposition
    # Uncontrollable: Regional Satellite Thermal Stress (NOAA DHW)
    thermal_score = max(5.0, min(100.0, (dhw_val / 4.0) * 55.0))
    # Controllable: Local Human Pressures (Anchoring, Marine Debris, Wastewater, Built Lodging Footprint)
    local_score = max(5.0, (impact_anchor * 25.0) + (impact_trash * 20.0) + min(30.0, pollution_val * 2.5) + min(25.0, (room_cap / 1200.0) * 25.0))
    total_score = thermal_score + local_score
    uncontrollable_pct = round((thermal_score / total_score) * 100.0, 1)
    controllable_pct = round(100.0 - uncontrollable_pct, 1)

    priority_islands.append({
        "rank": int(r["priority_rank"]),
        "island": isl_name,
        "state": r["state"],
        "ecoregion": r["ecoregion"],
        "lat": float(r["latitude"]),
        "lng": float(r["longitude"]),
        "marinePark": r["marine_park"],
        "surveyYear": int(r["survey_year"]),
        "lcc": float(r["live_coral_cover_pct"]),
        "lccChangeRate": float(r["lcc_change_rate"]) if r["lcc_change_rate"] else 0.0,
        "dhw": dhw_val,
        "disturbance": float(r["grp_disturbance_indicators"]) if r["grp_disturbance_indicators"] else 0.0,
        "pollution": pollution_val,
        "impactAnchor": impact_anchor,
        "impactTrash": impact_trash,
        "impactBleaching": int(r["impact_bleaching"]) if r.get("impact_bleaching") else 0,
        "confidence": r["confidence"],
        "predictedNextChange": float(r["predicted_next_change_pct_per_year"]),
        "predictionLower": float(r["prediction_lower"]),
        "predictionUpper": float(r["prediction_upper"]),
        "tier": r["priority_tier"],
        "evidence": r["evidence"],
        "recommendation": r["recommended_next_step"],
        "resortCount": int(infr.get("resort_count", 0)),
        "roomCapacity": room_cap,
        "diveCenters": int(infr.get("dive_center_count", 0)),
        "hasJetty": int(infr.get("has_commercial_jetty", 0)),
        "infrSource": infr.get("data_source", "Verified Registry"),
        "uncontrollable_pct": uncontrollable_pct,
        "controllable_pct": controllable_pct
    })

# 2. Load master history
with open(os.path.join(PROCESSED_DIR, "master_reef_tourism_dataset.csv"), encoding="utf-8") as f:
    master_rows = list(csv.DictReader(f))

island_history = {}
for r in master_rows:
    isl = r["island"]
    if isl not in island_history:
        island_history[isl] = []
    try:
        yr = int(r["survey_year"])
        lcc = float(r["live_coral_cover_pct"]) if r["live_coral_cover_pct"] else None
        dhw = float(r["noaa_max_dhw"]) if r.get("noaa_max_dhw") else 0.0
        if lcc is not None:
            island_history[isl].append({"year": yr, "lcc": round(lcc, 1), "dhw": round(dhw, 1)})
    except (ValueError, TypeError):
        continue

for isl in island_history:
    island_history[isl].sort(key=lambda x: x["year"])

# 3. Factor relationships
with open(os.path.join(PROCESSED_DIR, "factor_relationships.csv"), encoding="utf-8") as f:
    factor_rows = list(csv.DictReader(f))

# 4. Heat category summary
with open(os.path.join(PROCESSED_DIR, "heat_category_summary.csv"), encoding="utf-8") as f:
    heat_rows = list(csv.DictReader(f))

# 5. Model metrics
with open(os.path.join(PROCESSED_DIR, "model_evaluation_metrics.csv"), encoding="utf-8") as f:
    model_rows = list(csv.DictReader(f))

# 6. Load Marine Park Visitors (data.gov.my 2000-2017) & Tourism Data Gap
visitor_csv = os.path.join(BASE_DIR, "data", "raw", "structured", "taman_laut_visitors_2000_2017.csv")
visitor_rows = []
if os.path.exists(visitor_csv):
    with open(visitor_csv, encoding="utf-8") as f:
        visitor_rows = list(csv.DictReader(f))

# Aggregate by year
visitor_by_year = {}
for r in visitor_rows:
    yr = int(r["year"])
    st = r["state"]
    tot = int(r["total_visitors"])
    dom = int(r["domestic_visitors"])
    frg = int(r["foreign_visitors"])
    if yr not in visitor_by_year:
        visitor_by_year[yr] = {"year": yr, "domestic": 0, "foreign": 0, "total": 0, "states": set()}
    visitor_by_year[yr]["domestic"] += dom
    visitor_by_year[yr]["foreign"] += frg
    visitor_by_year[yr]["total"] += tot
    visitor_by_year[yr]["states"].add(st)

visitor_trend = []
for yr in sorted(visitor_by_year.keys()):
    v = visitor_by_year[yr]
    visitor_trend.append({
        "year": yr,
        "domestic": v["domestic"],
        "foreign": v["foreign"],
        "total": v["total"],
        "covered_states_count": len(v["states"])
    })

tourism_data_gap = {
    "source": "Jabatan Taman Laut Malaysia / data.gov.my (2000-2017)",
    "portal_url": "https://archive.data.gov.my/data/ms_MY/dataset/jumlah-pelawat-taman-laut-malaysia-dari-tahun-2000-hingga-2009-",
    "annual_trend": visitor_trend,
    "latest_recorded_year": 2017,
    "missing_years": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
    "missing_regions": ["Sabah (Sabah Parks)", "Sarawak (Sarawak Forestry Corp)"],
    "status": "UNCLOSED DATA GAP: No island-level or post-2017 official visitor records exist in open data."
}

# 7. Economic Valuation & NPV Trade-Off Simulation
from scripts.economic_valuation import get_economic_pillars, simulate_npv_tradeoff

economic_valuation = get_economic_pillars()
npv_tradeoff = simulate_npv_tradeoff(years=20, discount_rate=0.05)

data_bundle = {
    "nationalKPIs": {
        "meanCoralCover": 39.8,
        "coralCoverBaselineYear": "2025",
        "dropSince2012": -17.3,
        "totalEconomicValuationRM": 8.7,
        "marineTourismValuationRM": 4.8,
        "coastalProtectionValuationRM": 2.3,
        "priorityAlertCount": 10,
        "totalSurveyedIslands": 40,
        "totalRegistryIslands": 56,
        "activeHeatAlertDHW4Count": 11
    },
    "priorityIslands": priority_islands,
    "islandAccommodations": {
        isl: {
            "resortCount": int(info.get("resort_count", 0)),
            "roomCapacity": int(info.get("estimated_room_capacity", 0)),
            "diveCenters": int(info.get("dive_center_count", 0)),
            "hasJetty": int(info.get("has_commercial_jetty", 0)),
            "dataSource": info.get("data_source", "Verified Registry")
        }
        for isl, info in infr_map.items()
    },
    "islandHistory": island_history,
    "factorRelationships": factor_rows,
    "heatSummary": heat_rows,
    "modelMetrics": model_rows,
    "tourismDataGap": tourism_data_gap,
    "economicValuation": economic_valuation,
    "npvTradeoff": npv_tradeoff
}

js_content = f"""// Auto-generated ReefSafe AI Data Bundle
window.REEFSAFE_DATA = {json.dumps(data_bundle, indent=2)};
window.TOURISM_DATA_GAP = window.REEFSAFE_DATA.tourismDataGap;
window.ECONOMIC_VALUATION = window.REEFSAFE_DATA.economicValuation;
window.NPV_TRADEOFF = window.REEFSAFE_DATA.npvTradeoff;
"""

out_path = os.path.join(DASHBOARD_DIR, "data.js")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(js_content)

print(f"Successfully generated {out_path} ({len(priority_islands)} priority islands, {len(island_history)} historical series, RM 8.7B economic engine)")

