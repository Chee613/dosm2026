"""Export the source-safe figures used by the report and dashboard."""

import csv
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import polars as pl


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.economic_valuation import load_dmpm_tev
from scripts.train_models import FEATURES


OUT = ROOT / "reports/figures"
OUTPUT = ROOT / "output"
OUT.mkdir(parents=True, exist_ok=True)


def save(fig, name):
    target = OUT / name
    fig.tight_layout()
    fig.savefig(target, dpi=200)
    plt.close(fig)
    print(f"Exported {target}")


def plot_tourism_gap():
    path = ROOT / "data/raw/structured/taman_laut_visitors_2000_2017.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        # All 90 rows match the five Department of Marine Park state datasets (2000-2017).
        source = list(csv.DictReader(stream))
    totals = {}
    for row in source:
        year = int(row["year"])
        totals.setdefault(year, [0, 0])
        totals[year][0] += int(row["domestic_visitors"])
        totals[year][1] += int(row["foreign_visitors"])
    years = sorted(totals)
    domestic = [totals[year][0] / 1000 for year in years]
    foreign = [totals[year][1] / 1000 for year in years]

    fig, axis = plt.subplots(figsize=(10, 4.5))
    axis.bar(years, domestic, label="Domestic ('000)", color="#0284c7")
    axis.bar(years, foreign, bottom=domestic, label="Foreign ('000)", color="#38bdf8")
    axis.axvspan(2017.5, 2025.5, color="#fee2e2")
    peak = max(a + b for a, b in zip(domestic, foreign))
    axis.text(2021.5, peak * 0.5, "No verified island-level series\nafter the cited 2000-2017 source",
              ha="center", color="#991b1b")
    axis.set(xlim=(1999.5, 2025.5), xlabel="Year", ylabel="Recorded visitors ('000)",
             title="Verified marine-park visitor context and data gap")
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    save(fig, "01_tourism_data_gap.png")


def plot_coral_trajectory():
    annual = pl.read_csv(ROOT / "data/processed/survey_year_summary.csv")
    paired = pl.read_csv(ROOT / "data/processed/paired_change_summary.csv").row(0, named=True)
    fig, axis = plt.subplots(figsize=(10, 4.5))
    axis.plot(annual["survey_year"], annual["mean_lcc"], marker="o", color="#0f766e")
    for row in annual.iter_rows(named=True):
        axis.annotate(f"n={row['surveyed_units']}", (row["survey_year"], row["mean_lcc"]),
                      xytext=(0, 7), textcoords="offset points", ha="center", fontsize=7)
    axis.axhline(40, color="#f59e0b", linestyle="--", label="40% reference")
    axis.set(
        xlabel="Survey year", ylabel="Mean live coral cover (%)",
        title=("Mean cover among sites surveyed each year\n"
               f"Paired 2024-2025 change: {paired['change_pp']:+.2f} pp across n={paired['paired_units']} sites"),
    )
    axis.legend()
    axis.grid(alpha=0.25)
    save(fig, "02_national_coral_cover_trajectory.png")


def plot_thermal_context():
    data = pl.read_csv(ROOT / "data/processed/master_reef_tourism_dataset.csv")
    annual = data.group_by("survey_year").agg(pl.col("noaa_max_dhw").mean().alias("mean_dhw")).sort("survey_year")
    fig, axis = plt.subplots(figsize=(10, 4.2))
    axis.bar(annual["survey_year"], annual["mean_dhw"], color="#ea580c")
    axis.axhline(4, color="#dc2626", linestyle="--", label="NOAA Alert Level 1 threshold (DHW >= 4)")
    axis.set(xlabel="Survey year", ylabel="Mean regional maximum DHW",
             title="NOAA Coral Reef Watch regional context - excluded from scored model")
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    save(fig, "03_satellite_thermal_stress_dhw.png")


def plot_economic_context():
    valuation = load_dmpm_tev()
    components = valuation["components"]
    fig, axis = plt.subplots(figsize=(10, 4.8))
    labels = [item["component"] for item in reversed(components)]
    values = [item["annual_value_myr"] / 1e9 for item in reversed(components)]
    bars = axis.barh(labels, values, color="#0f766e")
    axis.bar_label(bars, labels=[f"RM{value:.3g}B" for value in values], padding=3)
    axis.set(xlabel="Published annual value (RM billion)",
             title="DMPM 2011-2015 TEV components - six evaluated archipelagos")
    axis.grid(axis="x", alpha=0.25)
    save(fig, "04_economic_valuation_pillars.png")


def plot_model_input_availability():
    data = pl.read_csv(ROOT / "data/processed/master_reef_tourism_dataset.csv")
    availability = sorted(
        ((feature, 100 * (1 - data[feature].null_count() / data.height)) for feature in FEATURES),
        key=lambda item: item[1],
    )
    fig, axis = plt.subplots(figsize=(10, 6))
    bars = axis.barh([item[0] for item in availability], [item[1] for item in availability], color="#0f766e")
    axis.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=7)
    axis.set(xlim=(0, 105), xlabel="Available before median imputation (%)",
             title="Verified scored-model input availability")
    axis.grid(axis="x", alpha=0.25)
    save(fig, "12_dataset_completeness_matrix.png")


def copy_model_figures():
    for source, target in (
        ("fig2_actual_vs_predicted.png", "07_actual_vs_predicted_oof.png"),
        ("fig3_feature_importance.png", "08_feature_importance.png"),
        ("fig1_model_performance_cv.png", "09_model_performance.png"),
        ("fig4_factor_relationships.png", "10_factor_relationships.png"),
        ("fig6_field_verification_priority_matrix.png", "13_field_verification_priority_matrix.png"),
    ):
        if (OUTPUT / source).exists():
            shutil.copy2(OUTPUT / source, OUT / target)


def main():
    plot_tourism_gap()
    plot_coral_trajectory()
    plot_thermal_context()
    plot_economic_context()
    copy_model_figures()
    plot_model_input_availability()


if __name__ == "__main__":
    main()
