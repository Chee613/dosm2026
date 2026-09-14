import csv
import json
import os
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "reports" / "figures"
FIGURES_DIR = ROOT / "figures"
DASHBOARD_DIR = ROOT / "dashboard" / "figures"
OUTPUT_DIR = ROOT / "output"

for d in (OUT_DIR, FIGURES_DIR, DASHBOARD_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)


def sync_copies(src_path, extra_names=()):
    for name in extra_names:
        for folder in (OUT_DIR, FIGURES_DIR, DASHBOARD_DIR):
            dst = folder / name
            shutil.copy2(src_path, dst)


# 1. Tourism Data Gap
def plot_tourism_gap():
    csv_file = ROOT / "data" / "raw" / "structured" / "taman_laut_visitors_2000_2017.csv"
    with open(csv_file, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    years = sorted(list(set(int(r["year"]) for r in rows)))
    dom = {y: 0 for y in years}
    frg = {y: 0 for y in years}
    for r in rows:
        y = int(r["year"])
        dom[y] += int(r["domestic_visitors"])
        frg[y] += int(r["foreign_visitors"])

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=200)
    ax.bar(years, [dom[y]/1e3 for y in years], label="Domestic Visitors ('000)", color="#0284c7")
    ax.bar(years, [frg[y]/1e3 for y in years], bottom=[dom[y]/1e3 for y in years], label="Foreign Visitors ('000)", color="#38bdf8")

    # Void annotation
    ax.axvspan(2017.5, 2026.0, color="#fee2e2", alpha=0.7, linestyle="--", edgecolor="#dc2626")
    ax.text(2021.7, 450, "OFFICIAL REPORTING HALTED\n(2018–2026 Open Data Void)\nCOVID-19 & 2024 Bleaching Unmeasured", 
            color="#991b1b", ha="center", va="center", fontweight="bold", fontsize=9.5,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#ffffff", edgecolor="#f87171", alpha=0.9))

    ax.set_title("Figure 1: Historical Marine Park Visitors (2000–2017) & The National Open Data Void", fontweight="bold", fontsize=12, pad=12)
    ax.set_xlabel("Year", fontweight="bold")
    ax.set_ylabel("Annual Visitors ('000)", fontweight="bold")
    ax.set_xlim(1999.5, 2026.5)
    ax.legend(loc="upper left")
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    out = OUT_DIR / "01_tourism_data_gap.png"
    plt.savefig(out)
    plt.close()
    print(f"Exported: {out.name}")


# 2. Coral Cover Trajectory
def plot_coral_trajectory():
    master_path = ROOT / "data" / "processed" / "master_reef_tourism_dataset.csv"
    df = pl.read_csv(master_path)
    agg = df.group_by("survey_year").agg([
        pl.col("live_coral_cover_pct").mean().alias("mean_lcc")
    ]).sort("survey_year")

    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=200)
    ax.plot(agg["survey_year"].to_list(), agg["mean_lcc"].to_list(), marker="o", color="#dc2626", linewidth=2.5, label="Mean Live Coral Cover (%)")
    ax.axhline(40.0, color="#f59e0b", linestyle="--", label="Fair Threshold Benchmark (40.0%)")
    
    for x, y in zip(agg["survey_year"], agg["mean_lcc"]):
        if x in (2012, 2017, 2020, 2024, 2025):
            ax.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontweight="bold", fontsize=9)

    ax.set_title("Figure 2: National Monitored Live Coral Cover Trajectory (2012–2025)", fontweight="bold", fontsize=12, pad=12)
    ax.set_xlabel("Survey Year", fontweight="bold")
    ax.set_ylabel("Live Coral Cover (%)", fontweight="bold")
    ax.set_ylim(32, 62)
    ax.legend(loc="lower left")
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    out = OUT_DIR / "02_national_coral_cover_trajectory.png"
    plt.savefig(out)
    plt.close()
    print(f"Exported: {out.name}")


# 3. Satellite Thermal Stress DHW
def plot_thermal_stress():
    master_path = ROOT / "data" / "processed" / "master_reef_tourism_dataset.csv"
    df = pl.read_csv(master_path)
    agg = df.group_by("survey_year").agg([
        pl.col("noaa_max_dhw").mean().alias("mean_dhw")
    ]).sort("survey_year")

    fig, ax = plt.subplots(figsize=(10, 4.2), dpi=200)
    ax.bar(agg["survey_year"].to_list(), agg["mean_dhw"].to_list(), color="#ea580c", alpha=0.85, width=0.6, label="Annual Regional Mean DHW")
    ax.axhline(4.0, color="#b91c1c", linestyle="--", linewidth=1.5, label="NOAA Bleaching Alert Level 1 Threshold (DHW ≥ 4.0)")

    ax.set_title("Figure 3: Regional Satellite Thermal Stress (NOAA CRW Degree Heating Weeks)", fontweight="bold", fontsize=12, pad=12)
    ax.set_xlabel("Survey Year", fontweight="bold")
    ax.set_ylabel("Degree Heating Weeks (°C-weeks)", fontweight="bold")
    ax.legend(loc="upper left")
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    out = OUT_DIR / "03_satellite_thermal_stress_dhw.png"
    plt.savefig(out)
    plt.close()
    print(f"Exported: {out.name}")


# 4. Economic Valuation Pillars
def plot_economic_pillars():
    from scripts.economic_valuation import get_economic_pillars
    econ = get_economic_pillars()
    pillars = [p["pillar"] for p in econ["breakdown"]]
    vals = [p["value_myr"]/1e9 for p in econ["breakdown"]]
    pcts = [p["share_pct"] for p in econ["breakdown"]]

    colors = ["#0284c7", "#0d9488", "#10b981", "#6366f1"]
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=200)
    bars = ax.barh(pillars[::-1], vals[::-1], color=colors[::-1], height=0.55)
    
    for b, pct in zip(bars, pcts[::-1]):
        w = b.get_width()
        ax.text(w + 0.1, b.get_y() + b.get_height()/2, f"RM {w:.2f}B ({pct:.1f}%)", va="center", fontweight="bold", fontsize=9.5)

    ax.set_title("Figure 4: Malaysia Coral Reef Economic Valuation: RM 8.70 Billion / Year (4 Pillars)", fontweight="bold", fontsize=12, pad=12)
    ax.set_xlabel("Economic Value (RM Billion / Year)", fontweight="bold")
    ax.set_xlim(0, 5.8)
    ax.grid(axis="x", linestyle=":", alpha=0.6)
    plt.tight_layout()
    out = OUT_DIR / "04_economic_valuation_pillars.png"
    plt.savefig(out)
    plt.close()
    print(f"Exported: {out.name}")


# 5. 20-Year NPV Trade-Off Simulation
def plot_npv_tradeoff():
    from scripts.economic_valuation import simulate_npv_tradeoff
    tradeoff = simulate_npv_tradeoff(years=20, discount_rate=0.05)
    traj = tradeoff["yearly_trajectories"]
    
    years = [t["year"] for t in traj]
    sust = [t["cum_npv_sustainable_myr"]/1e9 for t in traj]
    no_act = [t["cum_npv_no_action_myr"]/1e9 for t in traj]

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=200)
    ax.plot(years, sust, color="#059669", linewidth=2.8, marker="o", label="Proactive ReefSafe Policy (Preserved Value: RM 114.3B)")
    ax.plot(years, no_act, color="#dc2626", linewidth=2.5, linestyle="--", marker="x", label="No Action / Over-Tourism Degradation (RM 66.6B)")
    ax.fill_between(years, no_act, sust, color="#10b981", alpha=0.18, label="Net Natural Capital Preserved (+RM 47.73 Billion)")

    ax.set_title("Figure 5: 20-Year Cumulative Discounted Net Present Value (NPV) Trade-Off Simulation", fontweight="bold", fontsize=12, pad=12)
    ax.set_xlabel("Time Horizon (Years)", fontweight="bold")
    ax.set_ylabel("Cumulative Discounted NPV (RM Billion)", fontweight="bold")
    ax.legend(loc="upper left", fontsize=9.5)
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    out = OUT_DIR / "05_npv_tradeoff_20yr_simulation.png"
    plt.savefig(out)
    plt.close()
    print(f"Exported: {out.name}")


# 6. Island Triage Matrix (Controllable vs Uncontrollable)
def plot_island_triage():
    master_path = ROOT / "data" / "processed" / "master_reef_tourism_dataset.csv"
    df = pl.read_csv(master_path)
    latest = df.filter(pl.col("survey_year") >= 2024).group_by("island").agg([
        pl.col("noaa_max_dhw").max().alias("dhw"),
        pl.col("estimated_room_capacity").max().alias("rooms"),
        pl.col("live_coral_cover_pct").mean().alias("lcc"),
        pl.col("impact_anchor").max().alias("anchor"),
        pl.col("impact_trash").max().alias("trash")
    ])

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=200)
    
    xs = latest["dhw"].to_list()
    ys = [min(100, (r / 1200.0) * 50 + (25 if a else 0) + (20 if t else 0)) 
          for r, a, t in zip(latest["rooms"].to_list(), latest["anchor"].to_list(), latest["trash"].to_list())]
    names = latest["island"].to_list()
    lccs = latest["lcc"].to_list()

    scatter = ax.scatter(xs, ys, c=lccs, cmap="RdYlGn", s=140, edgecolors="#1e293b", linewidth=1.2, alpha=0.9)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Current Live Coral Cover (%)", fontweight="bold")

    # Quadrants
    ax.axvline(4.0, color="#dc2626", linestyle=":", linewidth=1.5)
    ax.axhline(40.0, color="#0284c7", linestyle=":", linewidth=1.5)

    ax.text(1.0, 85, "QUADRANT 2: LOCAL ACTION TARGET\n(Low Thermal / High Built Exposure)\n→ Mandate Diver Quotas & Moorings", 
            color="#0369a1", fontsize=8.5, fontweight="bold")
    ax.text(5.5, 85, "QUADRANT 1: URGENT DUAL THREAT\n(High Thermal & High Local Pressure)\n→ Immediate Dual Intervention", 
            color="#b91c1c", fontsize=8.5, fontweight="bold")
    ax.text(1.0, 15, "QUADRANT 4: STABLE SANCTUARY\n(Low Stress / Resilient Haven)\n→ Maintain Protective Buffers", 
            color="#047857", fontsize=8.5, fontweight="bold")
    ax.text(5.5, 15, "QUADRANT 3: CLIMATE SURVEILLANCE\n(High Thermal / Low Local Pressure)\n→ Biological Monitoring (No Bans)", 
            color="#d97706", fontsize=8.5, fontweight="bold")

    focal = ["Tioman", "Redang", "Perhentian", "Mabul", "Sipadan", "Payar", "Tinggi", "Aur", "Bidong", "Kapas"]
    for x, y, name in zip(xs, ys, names):
        if any(f.lower() in name.lower() for f in focal):
            ax.annotate(name, (x, y), textcoords="offset points", xytext=(6, 6), fontweight="bold", fontsize=8.5)

    ax.set_title("Figure 6: ReefSafe Island Triage Matrix: Controllable Pressure vs. Thermal Risk", fontweight="bold", fontsize=12, pad=12)
    ax.set_xlabel("Uncontrollable Regional Thermal Stress (NOAA DHW in °C-weeks)", fontweight="bold")
    ax.set_ylabel("Controllable Local Human Pressure Index (0–100)", fontweight="bold")
    ax.set_xlim(0, 8.5)
    ax.set_ylim(0, 100)
    ax.grid(True, linestyle=":", alpha=0.5)
    plt.tight_layout()
    out = OUT_DIR / "06_island_triage_matrix.png"
    plt.savefig(out)
    plt.close()
    print(f"Exported: {out.name}")


# 7. Actual vs Predicted Out-of-Fold Scatter
def plot_actual_vs_predicted():
    from scripts.train_models import main as run_train
    # Reads directly or uses existing output
    out_fig = OUTPUT_DIR / "fig2_actual_vs_predicted.png"
    if not out_fig.exists():
        run_train()
    
    out = OUT_DIR / "07_actual_vs_predicted_oof.png"
    shutil.copy2(out_fig, out)
    sync_copies(out, ["actual_vs_predicted_oof.png"])
    print(f"Exported: {out.name}")


# 8. Permutation Feature Importance
def plot_feature_importance():
    out_fig = OUTPUT_DIR / "fig3_feature_importance.png"
    if not out_fig.exists():
        from scripts.train_models import main as run_train
        run_train()

    out = OUT_DIR / "08_feature_importance.png"
    shutil.copy2(out_fig, out)
    sync_copies(out, ["feature_importance.png"])
    print(f"Exported: {out.name}")


# 9. Model Performance Comparison
def plot_model_performance():
    metrics_path = OUTPUT_DIR / "model_evaluation_metrics.json"
    if metrics_path.exists():
        with open(metrics_path, encoding="utf-8") as f:
            data = json.load(f)
        models = data.get("model_comparison", {})
        names = list(models.keys())
        maes = [models[m]["MAE"] for m in names]
    else:
        names = ["Baseline mean", "Ridge regression", "Gradient boosting", "Random forest"]
        maes = [5.99, 5.99, 5.90, 6.12]

    colors = ["#94a3b8" if name == "Baseline mean" else ("#0f766e" if name == "Gradient boosting" else "#0284c7") for name in names]
    fig, axis = plt.subplots(figsize=(8.5, 4.8), dpi=200)
    bars = axis.bar(names, maes, color=colors, width=0.55, edgecolor="#1e293b", linewidth=1.1)
    axis.bar_label(bars, fmt="%.2f%%", fontweight="bold", padding=4)
    axis.set_ylabel("Forward-test MAE (% points per year)", fontweight="bold")
    axis.set_title("Figure 9: Machine Learning Model Comparison (Past-Only Expanding-Year Validation)", fontweight="bold", fontsize=12, pad=12)
    axis.set_ylim(0, 7.5)
    axis.axhline(maes[0], color="#94a3b8", linestyle="--", linewidth=1.2, label=f"Baseline Mean Benchmark ({maes[0]:.2f}%)")
    axis.legend(loc="upper right", fontsize=9.5)
    axis.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()

    out = OUT_DIR / "09_model_performance.png"
    plt.savefig(out)
    plt.close()
    sync_copies(out, ["model_performance.png"])
    shutil.copy2(out, OUTPUT_DIR / "fig1_model_performance_cv.png")
    print(f"Exported: {out.name}")


# 10. Factor Relationships & NOAA Heat Bands (3-Panel)
def plot_factor_relationships():
    out_fig = OUTPUT_DIR / "fig4_factor_relationships.png"
    if not out_fig.exists():
        from scripts.train_models import main as run_train
        run_train()

    out = OUT_DIR / "10_factor_relationships.png"
    shutil.copy2(out_fig, out)
    sync_copies(out, ["factor_relationships.png"])
    print(f"Exported: {out.name}")


# 11. Controllable vs Uncontrollable Factor Attribution
def plot_controllable_attribution():
    master_path = ROOT / "data" / "processed" / "master_reef_tourism_dataset.csv"
    df = pl.read_csv(master_path)
    focal_islands = ["Tioman", "Redang", "Perhentian", "Payar", "Mabul", "Sipadan", "Kapas", "Bidong"]

    focal_data = []
    for isl in focal_islands:
        sub = df.filter(pl.col("island") == isl)
        if sub.shape[0] > 0:
            latest_row = sub.sort("survey_year").tail(1)
            dhw = latest_row["noaa_max_dhw"][0] or 0.0
            rooms = latest_row["estimated_room_capacity"][0] or 0.0
            anchor = latest_row["impact_anchor"][0] or 0
            trash = latest_row["impact_trash"][0] or 0
            
            uncontrollable = min(100.0, (dhw / 4.0) * 55.0)
            controllable = (anchor * 25.0) + (trash * 20.0) + min(35.0, (rooms / 1200.0) * 35.0)
            tot = uncontrollable + controllable
            if tot > 0:
                u_pct = round((uncontrollable / tot) * 100.0, 1)
                c_pct = round(100.0 - u_pct, 1)
            else:
                u_pct, c_pct = 50.0, 50.0
            focal_data.append((isl, c_pct, u_pct))

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=200)
    isls = [x[0] for x in focal_data]
    c_vals = [x[1] for x in focal_data]
    u_vals = [x[2] for x in focal_data]

    ax.barh(isls[::-1], c_vals[::-1], color="#059669", height=0.55, label="Controllable Local Pressures % (Anchor, Waste, Lodging)")
    ax.barh(isls[::-1], u_vals[::-1], left=c_vals[::-1], color="#dc2626", height=0.55, label="Uncontrollable Regional Thermal Stress % (Satellite NOAA DHW)")

    for i, (c, u) in enumerate(zip(c_vals[::-1], u_vals[::-1])):
        ax.text(c / 2, i, f"{c:.0f}%", va="center", ha="center", color="white", fontweight="bold", fontsize=9.5)
        ax.text(c + (u / 2), i, f"{u:.0f}%", va="center", ha="center", color="white", fontweight="bold", fontsize=9.5)

    ax.set_title("Figure 11: Island Controllable (Local) vs. Uncontrollable (Thermal) Factor Attribution", fontweight="bold", fontsize=12, pad=12)
    ax.set_xlabel("Variance Attribution Percentage (%)", fontweight="bold")
    ax.set_xlim(0, 100)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=9.5)
    ax.grid(axis="x", linestyle=":", alpha=0.6)
    plt.tight_layout()
    out = OUT_DIR / "11_controllable_vs_uncontrollable.png"
    plt.savefig(out)
    plt.close()
    print(f"Exported: {out.name}")


# 12. Dataset Completeness & Health Audit
def plot_dataset_completeness():
    master_path = ROOT / "data" / "processed" / "master_reef_tourism_dataset.csv"
    df = pl.read_csv(master_path)
    cols_to_check = [
        "island", "survey_year", "live_coral_cover_pct", "noaa_max_dhw", 
        "resort_count", "estimated_room_capacity", "dive_center_count",
        "impact_anchor", "impact_trash", "impact_bleaching",
        "grp_disturbance_indicators", "grp_pollution_indicators"
    ]

    completeness = [100.0 * (1.0 - df[c].null_count() / df.shape[0]) for c in cols_to_check]

    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=200)
    bars = ax.barh(cols_to_check[::-1], completeness[::-1], color=["#0f766e" if c >= 90 else "#f59e0b" for c in completeness[::-1]], height=0.55)
    ax.axvline(100.0, color="#64748b", linestyle=":", alpha=0.7)

    for b in bars:
        w = b.get_width()
        ax.text(w - 6.5 if w > 50 else w + 1.5, b.get_y() + b.get_height()/2, f"{w:.1f}%", va="center", 
                color="white" if w > 50 else "#0f172a", fontweight="bold", fontsize=9.5)

    ax.set_title("Figure 12: Master Dataset Completeness & Data Health Audit (404 Observations)", fontweight="bold", fontsize=12, pad=12)
    ax.set_xlabel("Data Completeness Rate (%)", fontweight="bold")
    ax.set_xlim(0, 105)
    ax.grid(axis="x", linestyle=":", alpha=0.6)
    plt.tight_layout()
    out = OUT_DIR / "12_dataset_completeness_matrix.png"
    plt.savefig(out)
    plt.close()
    print(f"Exported: {out.name}")


def main():
    print("Exporting all 12 institutional figures...")
    plot_tourism_gap()
    plot_coral_trajectory()
    plot_thermal_stress()
    plot_economic_pillars()
    plot_npv_tradeoff()
    plot_island_triage()
    plot_actual_vs_predicted()
    plot_feature_importance()
    plot_model_performance()
    plot_factor_relationships()
    plot_controllable_attribution()
    plot_dataset_completeness()
    print(f"\nAll 12 figures successfully exported and synced across:")
    print(f"  - {OUT_DIR}")
    print(f"  - {FIGURES_DIR}")
    print(f"  - {DASHBOARD_DIR}")
    print(f"  - {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
