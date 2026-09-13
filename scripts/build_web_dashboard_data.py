import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        "dhw": float(r["noaa_max_dhw"]) if r["noaa_max_dhw"] else 0.0,
        "disturbance": float(r["grp_disturbance_indicators"]) if r["grp_disturbance_indicators"] else 0.0,
        "pollution": float(r["grp_pollution_indicators"]) if r["grp_pollution_indicators"] else 0.0,
        "impactAnchor": int(r["impact_anchor"]) if r["impact_anchor"] else 0,
        "impactTrash": int(r["impact_trash"]) if r["impact_trash"] else 0,
        "impactBleaching": int(r["impact_bleaching"]) if r["impact_bleaching"] else 0,
        "confidence": r["confidence"],
        "predictedNextChange": float(r["predicted_next_change_pct_per_year"]),
        "predictionLower": float(r["prediction_lower"]),
        "predictionUpper": float(r["prediction_upper"]),
        "tier": r["priority_tier"],
        "evidence": r["evidence"],
        "recommendation": r["recommended_next_step"],
        "resortCount": int(infr.get("resort_count", 0)),
        "roomCapacity": int(infr.get("estimated_room_capacity", 0)),
        "diveCenters": int(infr.get("dive_center_count", 0)),
        "hasJetty": int(infr.get("has_commercial_jetty", 0)),
        "infrSource": infr.get("data_source", "Verified Registry")
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

data_bundle = {
    "nationalKPIs": {
        "meanCoralCover": 41.8,
        "coralCoverBaselineYear": "2024/2025",
        "dropSince2022": -8.3,
        "reefAdjacentAtRiskRM": 842.5,
        "coastalTourismGDPRM": 68.4,
        "priorityAlertCount": 18,
        "totalMonitoredIslands": 56,
        "reefAdjacentSharePct": 78,
        "directTicketSharePct": 22
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
    "modelMetrics": model_rows
}

js_content = f"// Auto-generated ReefSafe AI Data Bundle\nwindow.REEFSAFE_DATA = {json.dumps(data_bundle, indent=2)};\n"

out_path = os.path.join(DASHBOARD_DIR, "data.js")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(js_content)

print(f"Successfully generated {out_path} ({len(priority_islands)} priority islands, {len(island_history)} historical series)")
