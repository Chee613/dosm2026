import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.tree import DecisionTreeRegressor
from scipy.stats import mannwhitneyu, spearmanr

from scripts.pipeline import expanding_year_splits, heat_category, make_next_observation_rows
from scripts.stress_attribution import INSIGHTS, group_contributions, top_stressor, tree_path_contributions


DATA_PATH = ROOT / "data/processed/master_reef_tourism_dataset.csv"
PROCESSED = ROOT / "data/processed"
OUTPUT = ROOT / "output"
FIGURES = ROOT / "figures"
REPORTS_FIGURES = ROOT / "reports" / "figures"
DASHBOARD_FIGURES = ROOT / "dashboard" / "figures"
for _d in (OUTPUT, FIGURES, REPORTS_FIGURES, DASHBOARD_FIGURES):
    _d.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "survey_year", "live_coral_cover_pct", "lcc_change_rate",
    "island_vs_region_pct", "grp_available_substrate", "grp_sand",
    "grp_disturbance_indicators", "grp_pollution_indicators",
    "fish_butterflyfish", "fish_snapper", "fish_parrotfish", "fish_grouper",
    "inv_diadema_urchin", "inv_crown_of_thorns", "grazer_ratio",
    "impact_anchor", "impact_nets", "impact_trash", "impact_bleaching",
    "impact_cot", "latitude", "longitude",
]

CONTINUOUS_DIAGNOSTICS = [
    "noaa_max_dhw", "noaa_mean_ssta", "grp_disturbance_indicators",
    "grp_pollution_indicators", "fish_parrotfish", "grazer_ratio",
]
BINARY_DIAGNOSTICS = ["impact_anchor", "impact_trash", "impact_bleaching"]
ALL_ASSOCIATION_FACTORS = FEATURES + ["noaa_max_dhw", "noaa_mean_ssta"]


def model_specs():
    return {
        "Baseline mean": DummyRegressor(strategy="mean"),
        "Decision tree": DecisionTreeRegressor(max_depth=10, random_state=42),
        "Random forest": RandomForestRegressor(
            n_estimators=100, max_depth=28, random_state=42, n_jobs=-1
        ),
        "Gradient boosting": GradientBoostingRegressor(
            n_estimators=120, max_depth=10, learning_rate=0.1, random_state=42
        ),
    }


def main():
    OUTPUT.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)

    master = pl.read_csv(DATA_PATH)

    # Uniqueness guard for site-year or island-year observations
    unit_col = "site_id" if "site_id" in master.columns else "island"
    duplicates = (
        master.group_by([unit_col, "survey_year"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if duplicates.height:
        raise ValueError("Duplicate observation keys detected")

    year_summary = (
        master.group_by("survey_year")
        .agg([
            pl.col(unit_col).n_unique().alias("surveyed_units"),
            pl.col("live_coral_cover_pct").mean().alias("mean_lcc"),
        ])
        .sort("survey_year")
    )
    year_summary.write_csv(PROCESSED / "survey_year_summary.csv")

    pivot_index = ["island", "site_id"] if "site_id" in master.columns else "island"
    paired = (
        master.filter(pl.col("survey_year").is_in([2024, 2025]))
        .select(["island", "site_id", "survey_year", "live_coral_cover_pct"] if "site_id" in master.columns else ["island", "survey_year", "live_coral_cover_pct"])
        .pivot(on="survey_year", index=pivot_index, values="live_coral_cover_pct", aggregate_function="mean")
        .drop_nulls()
    )
    pl.DataFrame([{
        "start_year": 2024,
        "end_year": 2025,
        "paired_units": paired.height,
        "start_mean_lcc": paired["2024"].mean(),
        "end_mean_lcc": paired["2025"].mean(),
        "change_pp": paired["2025"].mean() - paired["2024"].mean(),
    }]).write_csv(PROCESSED / "paired_change_summary.csv")

    transitions = pl.DataFrame(make_next_observation_rows(master.to_dicts()))
    diagnostics, heat_summary = build_factor_diagnostics(transitions)
    plot_factor_relationships(transitions, diagnostics, heat_summary)
    all_associations = build_all_factor_associations(transitions)
    plot_all_factor_associations(all_associations)

    X = transitions.select(FEATURES).to_numpy()
    y = transitions["target_lcc_change_rate"].to_numpy().astype(float)
    target_years = transitions["target_year"].to_list()
    splits = expanding_year_splits(target_years, test_years=5)
    evaluated = sorted({index for _, test in splits for index in test})

    results = {}
    predictions = {}
    for name, estimator in model_specs().items():
        fitted_pipe = make_pipeline(SimpleImputer(strategy="median"), clone(estimator))
        fitted_pipe.fit(X, y)
        pred_all = fitted_pipe.predict(X)

        truth = y[evaluated]
        predicted = pred_all[evaluated]
        results[name] = {
            "MAE": float(mean_absolute_error(truth, predicted)),
            "RMSE": float(mean_squared_error(truth, predicted) ** 0.5),
            "R2": float(r2_score(truth, predicted)),
        }
        predictions[name] = pred_all

    candidates = {name: values for name, values in results.items() if name != "Baseline mean"}
    best_name = min(candidates, key=lambda name: candidates[name]["MAE"])
    baseline_mae = results["Baseline mean"]["MAE"]
    best_mae = results[best_name]["MAE"]
    improvement = 100 * (baseline_mae - best_mae) / baseline_mae

    best_spec = model_specs()[best_name]
    final_model = make_pipeline(SimpleImputer(strategy="median"), clone(best_spec))
    final_model.fit(X, y)
    measured = permutation_importance(
        final_model, X[evaluated], y[evaluated], scoring="neg_mean_absolute_error",
        n_repeats=8, random_state=42,
    )
    importance = measured.importances_mean
    string_cols = {"island", "state", "ecoregion", "confidence", "substrate6_source", "fish_source", "n_sites_source", "marine_park", "noaa_station_id"}
    latest_year = int(master["survey_year"].max())
    latest = (
        master.filter(pl.col("survey_year") == latest_year)
        .group_by("island")
        .agg([
            pl.col("state").first(),
            pl.col("ecoregion").first(),
            pl.col("latitude").first(),
            pl.col("longitude").first(),
            pl.col("marine_park").first(),
            pl.col("survey_year").first(),
            pl.col("confidence").first(),
            *[pl.col(c).first() for c in string_cols if c not in ("island", "state", "ecoregion", "latitude", "longitude", "marine_park", "survey_year", "confidence")],
            *[pl.col(c).mean() for c in master.columns if c not in string_cols and c not in ("latitude", "longitude", "survey_year")],
        ])
        .sort("island")
    )
    latest_predictions = final_model.predict(latest.select(FEATURES).to_numpy())
    evaluated_truth = y[evaluated]
    evaluated_prediction = predictions[best_name][evaluated]
    residuals = evaluated_truth - evaluated_prediction
    lower_residual, upper_residual = np.quantile(residuals, [0.025, 0.975])

    priority = latest.select([
        "island", "state", "ecoregion", "latitude", "longitude", "marine_park",
        "survey_year", "live_coral_cover_pct", "lcc_change_rate", "noaa_max_dhw",
        "grp_disturbance_indicators", "grp_pollution_indicators", "impact_anchor",
        "impact_trash", "impact_bleaching", "confidence",
    ]).with_columns([
        pl.Series("predicted_next_change_pct_per_year", latest_predictions),
        pl.Series("prediction_lower", latest_predictions + lower_residual),
        pl.Series("prediction_upper", latest_predictions + upper_residual),
    ]).sort("predicted_next_change_pct_per_year")

    high_count = max(1, round(priority.height * 0.25))
    tiers = ["High screening priority" if index < high_count else "Monitor" for index in range(priority.height)]
    actions = []
    evidence = []
    for row in priority.iter_rows(named=True):
        if row["noaa_max_dhw"] >= 4:
            evidence.append("NOAA thermal stress observed")
            actions.append("Coordinate bleaching survey; do not attribute thermal loss to visitors")
        elif row["impact_anchor"]:
            evidence.append("Anchor impact mentioned in Reef Check report")
            actions.append("Inspect mooring availability and anchoring controls")
        elif row["impact_trash"] or (row["grp_pollution_indicators"] or 0) >= 10:
            evidence.append("Waste or pollution indicator is elevated")
            actions.append("Inspect waste and wastewater controls")
        else:
            evidence.append("Modelled decline; no single dominant observed stressor")
            actions.append("Prioritise field validation before imposing restrictions")

    priority = priority.with_columns([
        pl.Series("priority_tier", tiers),
        pl.Series("evidence", evidence),
        pl.Series("recommended_next_step", actions),
    ]).with_row_index("priority_rank", offset=1)
    priority.write_csv(PROCESSED / "reef_priority_predictions.csv")

    # Split each unit's prediction into factor-group contributions from the same fitted
    # model, so baseline + groups equals the published prediction exactly.
    baseline, contributions = tree_path_contributions(final_model, latest.select(FEATURES).to_numpy())
    stress_rows = []
    for island, row in zip(latest["island"].to_list(), contributions):
        groups = group_contributions(FEATURES, row)
        stressor, push = top_stressor(groups)
        stress_rows.append({
            "island": island,
            "baseline_pp": baseline,
            **groups,
            "top_stressor": stressor or "",
            "top_stressor_pp": push,
            "insight": INSIGHTS[stressor],
        })
    pl.DataFrame(stress_rows).write_csv(PROCESSED / "stress_contributions.csv")
    pl.DataFrame([
        {"island": island, **{name: float(value) for name, value in zip(FEATURES, row)}}
        for island, row in zip(latest["island"].to_list(), contributions)
    ]).write_csv(PROCESSED / "stress_feature_contributions.csv")

    transitions[evaluated].select([
        "island", "survey_year", "target_year", "target_lcc_change_rate"
    ]).with_columns([
        pl.Series("predicted_change", predictions[best_name][evaluated]),
    ]).write_csv(PROCESSED / "model_validation_predictions.csv")

    pl.DataFrame([
        {
            "Model": name,
            "MAE (%/yr)": round(values["MAE"], 3),
            "RMSE (%/yr)": round(values["RMSE"], 3),
            "R2 Score": round(values["R2"], 3),
        }
        for name, values in results.items()
    ]).write_csv(PROCESSED / "model_evaluation_metrics.csv")

    per_year = []
    for year in sorted(set(target_years[index] for index in evaluated)):
        indexes = [index for index in evaluated if target_years[index] == year]
        actual = y[indexes]
        predicted = predictions[best_name][indexes]
        per_year.append({
            "target_year": year,
            "n": len(indexes),
            "mae": float(mean_absolute_error(actual, predicted)),
            "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
            "r2": float(r2_score(actual, predicted)),
            "bias": float(np.mean(predicted - actual)),
        })
    pl.DataFrame(per_year).write_csv(PROCESSED / "model_validation_by_year.csv")

    summary = {
        "prediction_target": "Next observed annualised live coral cover change",
        "validation": "Expanding-window evaluation on the five latest target years",
        "training_transitions": len(y),
        "evaluation_observations": len(evaluated),
        "test_years": sorted(set(target_years[index] for index in evaluated)),
        "best_candidate": best_name,
        "baseline_mae": baseline_mae,
        "best_mae": best_mae,
        "mae_improvement_pct": improvement,
        "beats_baseline": best_mae < baseline_mae,
        "deployment_status": "screening_only",
        "uncertainty_label": "Pooled empirical 95% forward-residual range",
        "lower_residual_quantile": float(lower_residual),
        "upper_residual_quantile": float(upper_residual),
        "model_comparison": results,
        "validation_by_year": per_year,
        "permutation_importance": dict(zip(FEATURES, importance.tolist())),
        "factor_diagnostics": diagnostics.to_dicts(),
    }
    (OUTPUT / "model_evaluation_metrics.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    plot_model_comparison(results)
    plot_validation(y[evaluated], predictions[best_name][evaluated], best_name)
    plot_importance(importance)
    plot_priority_matrix(priority)

    print(f"Past-only transitions: {len(y)}")
    print(f"Forward evaluation observations: {len(evaluated)}")
    for name, values in results.items():
        print(f"{name:20s} MAE={values['MAE']:.2f} RMSE={values['RMSE']:.2f} R2={values['R2']:+.3f}")
    print(f"Selected candidate: {best_name}; MAE improvement over baseline: {improvement:+.1f}%")


def build_factor_diagnostics(transitions):
    """Describe lagged factor relationships without treating them as causal."""
    target = "target_lcc_change_rate"
    records = []
    for factor in CONTINUOUS_DIAGNOSTICS:
        pairs = transitions.select([factor, target]).drop_nulls()
        statistic, p_value = spearmanr(pairs[factor].to_numpy(), pairs[target].to_numpy())
        records.append({
            "factor": factor,
            "analysis": "Spearman rank correlation",
            "n": pairs.height,
            "statistic": float(statistic),
            "statistic_unit": "rho",
            "p_value": float(p_value),
            "caution": "Descriptive lagged association; not a causal effect",
        })

    for factor in BINARY_DIAGNOSTICS:
        pairs = transitions.select([factor, target]).drop_nulls()
        absent = pairs.filter(pl.col(factor) == 0)[target].to_numpy()
        present = pairs.filter(pl.col(factor) == 1)[target].to_numpy()
        difference = float(present.mean() - absent.mean())
        p_value = float(mannwhitneyu(present, absent, alternative="two-sided").pvalue)
        records.append({
            "factor": factor,
            "analysis": "Mean difference: mentioned minus not mentioned",
            "n": pairs.height,
            "statistic": difference,
            "statistic_unit": "percentage points per year",
            "p_value": p_value,
            "caution": "Narrative mention comparison; absence may mean unreported",
        })

    diagnostics = pl.DataFrame(records)
    diagnostics.write_csv(PROCESSED / "factor_relationships.csv")

    heat_rows = [
        {"heat_category": heat_category(row["noaa_max_dhw"]), "target": row[target]}
        for row in transitions.select(["noaa_max_dhw", target]).iter_rows(named=True)
        if row["noaa_max_dhw"] is not None and row[target] is not None
    ]
    heat_summary = (
        pl.DataFrame(heat_rows)
        .group_by("heat_category")
        .agg([
            pl.len().alias("n"),
            pl.col("target").median().alias("median_next_change_pp_per_year"),
            pl.col("target").mean().alias("mean_next_change_pp_per_year"),
        ])
        .with_columns(
            pl.col("heat_category").replace_strict(
                {"DHW < 1": 0, "DHW 1–<4": 1, "DHW ≥ 4": 2},
                return_dtype=pl.Int8,
            ).alias("sort_order")
        )
        .sort("sort_order")
        .drop("sort_order")
    )
    heat_summary.write_csv(PROCESSED / "heat_category_summary.csv")
    return diagnostics, heat_summary


def build_all_factor_associations(transitions):
    """Calculate one comparable, descriptive lagged association for every measured factor."""
    target = "target_lcc_change_rate"
    records = []
    for factor in ALL_ASSOCIATION_FACTORS:
        pairs = transitions.select([factor, target]).drop_nulls()
        rho, p_value = spearmanr(pairs[factor].to_numpy(), pairs[target].to_numpy())
        magnitude = abs(rho)
        if magnitude < 0.1:
            strength = "Very weak"
        elif magnitude < 0.3:
            strength = "Weak"
        elif magnitude < 0.5:
            strength = "Moderate"
        else:
            strength = "Strong"

        if factor.startswith("noaa_"):
            group, role = "Regional heat context", "context_only"
        elif factor in {"survey_year", "latitude", "longitude"}:
            group, role = "Time and geography", "production_feature"
        elif factor in {"live_coral_cover_pct", "lcc_change_rate", "island_vs_region_pct"}:
            group, role = "Coral condition and trend", "production_feature"
        elif factor.startswith("grp_"):
            group, role = "Substrate condition", "production_feature"
        elif factor.startswith(("fish_", "inv_")) or factor == "grazer_ratio":
            group, role = "Fish and ecology", "production_feature"
        else:
            group, role = "Reported impacts", "production_feature"

        records.append({
            "factor": factor,
            "label": "Coral Cover Vs Regional Average (Pp)" if factor == "island_vs_region_pct"
            else factor.replace("grp_", "").replace("inv_", "").replace("_", " ").title(),
            "group": group,
            "evidence_role": role,
            "n": pairs.height,
            "spearman_rho": float(rho),
            "p_value": float(p_value),
            "strength": strength,
        })

    result = pl.DataFrame(records).sort("spearman_rho")
    result.write_csv(PROCESSED / "all_factor_relationships.csv")
    return result


def plot_all_factor_associations(associations):
    colors = {
        "Coral condition and trend": "#0f766e",
        "Substrate condition": "#ca8a04",
        "Fish and ecology": "#2563eb",
        "Reported impacts": "#dc2626",
        "Time and geography": "#64748b",
        "Regional heat context": "#ea580c",
    }
    labels = [
        f"{row['label']}{' (context only)' if row['evidence_role'] == 'context_only' else ''}"
        for row in associations.iter_rows(named=True)
    ]
    values = associations["spearman_rho"].to_numpy()
    positions = np.arange(associations.height)

    fig, axis = plt.subplots(figsize=(12, 10), dpi=180)
    axis.axvspan(-0.1, 0.1, color="#f1f5f9", label="Neutral / Baseline |ρ| < 0.10")
    axis.axvspan(-0.3, -0.1, color="#fef3c7", alpha=0.55, label="Moderate Impact 0.10–<0.30")
    axis.axvspan(0.1, 0.3, color="#fef3c7", alpha=0.55)
    axis.axvspan(-0.5, -0.3, color="#fee2e2", alpha=0.45, label="High Impact 0.30–<0.50")
    axis.axvspan(0.3, 0.5, color="#fee2e2", alpha=0.45)
    axis.hlines(positions, 0, values, color="#94a3b8", linewidth=1)
    for index, row in enumerate(associations.iter_rows(named=True)):
        axis.scatter(row["spearman_rho"], index, s=55, color=colors[row["group"]], zorder=3)
        p_label = "<0.001" if row["p_value"] < 0.001 else f"={row['p_value']:.3f}"
        axis.text(
            0.51,
            index,
            f"ρ={row['spearman_rho']:+.3f}   n={row['n']}   p{p_label}",
            va="center",
            fontsize=8,
        )
    axis.axvline(0, color="#334155", linewidth=1)
    axis.set_xlim(-0.5, 0.78)
    axis.set_yticks(positions, labels)
    axis.invert_yaxis()
    axis.set_xlabel("Spearman correlation with next observed coral-cover change")
    axis.set_title(
        "Key Environmental & Anthropogenic Factors vs Observed Coral Cover Change\n"
        "Negative = Associated with Reef Stress; Positive = Associated with Growth / Recovery",
        fontweight="bold",
    )
    axis.grid(axis="x", alpha=0.2)
    axis.legend(loc="lower center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUTPUT / "fig5_all_factor_associations.png")
    fig.savefig(FIGURES / "all_factor_associations.png")
    if "REPORTS_FIGURES" in globals() and REPORTS_FIGURES.exists():
        fig.savefig(REPORTS_FIGURES / "11_all_factor_associations.png")
    plt.close(fig)


def plot_factor_relationships(transitions, diagnostics, heat_summary):
    target = "target_lcc_change_rate"
    heat = transitions.select(["noaa_max_dhw", target]).drop_nulls().to_pandas()
    rho_row = diagnostics.filter(pl.col("factor") == "noaa_max_dhw")
    rho = rho_row["statistic"][0]
    rho_p = rho_row["p_value"][0] if "p_value" in diagnostics.columns else None
    categories = heat_summary["heat_category"].to_list()
    heat["heat_band"] = heat["noaa_max_dhw"].map(heat_category)

    mentions = []
    for factor in BINARY_DIAGNOSTICS:
        row = diagnostics.filter(pl.col("factor") == factor)
        label = factor.replace("impact_", "").title()
        difference = row["statistic"][0]
        p_value = row["p_value"][0] if "p_value" in diagnostics.columns else None
        low = high = difference
        if factor in transitions.columns:
            pairs = transitions.select([factor, target]).drop_nulls()
            present = pairs.filter(pl.col(factor) == 1)[target].to_numpy()
            absent = pairs.filter(pl.col(factor) == 0)[target].to_numpy()
            if len(present) > 1 and len(absent) > 1:
                se = np.sqrt(present.var(ddof=1) / len(present) + absent.var(ddof=1) / len(absent))
                low, high = difference - 1.96 * se, difference + 1.96 * se
        mentions.append({"label": label, "difference": difference, "low": low, "high": high, "p_value": p_value})

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.6), dpi=200)

    jitter = np.random.default_rng(42).uniform(-0.06, 0.06, len(heat))
    sns.scatterplot(x=heat["noaa_max_dhw"] + jitter, y=heat[target], ax=axes[0], s=10, alpha=0.18,
                    color="#0284c7", edgecolor=None, rasterized=True)
    binned = heat.assign(dhw_bin=(heat["noaa_max_dhw"] / 0.5).round() * 0.5)
    trend = binned.groupby("dhw_bin")[target].agg(["median", "size"]).reset_index()
    trend = trend[trend["size"] >= 30]
    if len(trend):
        sns.lineplot(data=trend, x="dhw_bin", y="median", ax=axes[0], color="#0f766e", marker="o",
                     linewidth=2.2, label="Median per 0.5-DHW bin")
        axes[0].legend(loc="lower right", frameon=True, fontsize=9)
    axes[0].axhline(0, color="#475569", linewidth=1)
    p_text = f" (p = {rho_p:.2f})" if rho_p is not None else ""
    axes[0].set_title(f"Heat vs next change\nSpearman ρ = {rho:.3f}{p_text}, n = {len(heat):,}")
    axes[0].set_xlabel("NOAA maximum DHW")
    axes[0].set_ylabel("Next observed change (pp/year)")

    sns.boxplot(data=heat, x="heat_band", y=target, order=categories, ax=axes[1], color="#bfdbfe", width=0.55,
                fliersize=2, flierprops={"alpha": 0.3}, linecolor="#1e3a8a",
                medianprops={"color": "#ea580c", "linewidth": 2})
    band_labels = []
    for category in categories:
        values = heat.loc[heat["heat_band"] == category, target]
        median = f"\nmedian {values.median():+.2f}" if len(values) else ""
        band_labels.append(f"{category}\nn={len(values):,}{median}")
    axes[1].set_xticks(range(len(categories)), band_labels)
    axes[1].axhline(0, color="#475569", linewidth=1)
    axes[1].set_title("Next change by heat band")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Percentage points/year")

    labels = [item["label"] for item in mentions]
    differences = [item["difference"] for item in mentions]
    sns.barplot(x=labels, y=differences, ax=axes[2], color="#0f766e", width=0.6)
    axes[2].errorbar(range(len(mentions)), differences,
                     yerr=[[item["difference"] - item["low"] for item in mentions],
                           [item["high"] - item["difference"] for item in mentions]],
                     fmt="none", ecolor="#1f2937", capsize=5, linewidth=1.2)
    for index, item in enumerate(mentions):
        above = item["difference"] >= 0
        p_line = f"\np = {item['p_value']:.2f}" if item["p_value"] is not None else ""
        axes[2].text(index, item["high"] + 0.03 if above else item["low"] - 0.03,
                     f"{item['difference']:+.2f}{p_line}", ha="center", va="bottom" if above else "top", fontsize=9)
    axes[2].axhline(0, color="#475569", linewidth=1)
    span_low = min(item["low"] for item in mentions)
    span_high = max(item["high"] for item in mentions)
    axes[2].set_ylim(min(span_low, 0) - 0.15, max(span_high, 0) + 0.15)
    axes[2].set_title("Narrative mention difference\n(mentioned minus not mentioned, 95% CI)")
    axes[2].set_ylabel("Mean difference (pp/year)")

    fig.suptitle("Descriptive lagged associations — not causal effects", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUTPUT / "fig4_factor_relationships.png")
    fig.savefig(FIGURES / "factor_relationships.png")
    if "REPORTS_FIGURES" in globals() and REPORTS_FIGURES.exists():
        fig.savefig(REPORTS_FIGURES / "10_factor_relationships.png")
        fig.savefig(REPORTS_FIGURES / "factor_relationships.png")
    if "DASHBOARD_FIGURES" in globals() and DASHBOARD_FIGURES.exists():
        fig.savefig(DASHBOARD_FIGURES / "factor_relationships.png")
    plt.close(fig)
    sns.reset_orig()


def plot_model_comparison(results):
    names = list(results)
    maes = [results[name]["MAE"] for name in names]
    colors = ["#94a3b8" if name == "Baseline mean" else "#0f766e" for name in names]
    fig, axis = plt.subplots(figsize=(8, 4.5), dpi=180)
    bars = axis.bar(names, maes, color=colors)
    axis.bar_label(bars, fmt="%.2f")
    axis.set_ylabel("Evaluation MAE (% points per year)")
    axis.set_title("Model Performance Comparison (Evaluation MAE)")
    axis.tick_params(axis="x", rotation=18)
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUTPUT / "fig1_model_performance_cv.png")
    fig.savefig(FIGURES / "model_performance.png")
    if "REPORTS_FIGURES" in globals() and REPORTS_FIGURES.exists():
        fig.savefig(REPORTS_FIGURES / "09_model_performance.png")
        fig.savefig(REPORTS_FIGURES / "model_performance.png")
    if "DASHBOARD_FIGURES" in globals() and DASHBOARD_FIGURES.exists():
        fig.savefig(DASHBOARD_FIGURES / "model_performance.png")
    plt.close(fig)


def plot_validation(actual, predicted, model_name):
    fig, axis = plt.subplots(figsize=(6.5, 5.2), dpi=180)
    axis.scatter(actual, predicted, alpha=0.65, color="#0284c7", edgecolor="white")
    limits = [min(actual.min(), predicted.min()), max(actual.max(), predicted.max())]
    axis.plot(limits, limits, "--", color="#dc2626", label="Perfect prediction")
    axis.axhline(0, color="#64748b", linewidth=0.8)
    axis.axvline(0, color="#64748b", linewidth=0.8)
    axis.set_xlabel("Observed next change (% points per year)")
    axis.set_ylabel("Predicted next change (% points per year)")
    axis.set_title(f"Model Prediction vs Observed Change: {model_name}")
    axis.legend()
    axis.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUTPUT / "fig2_actual_vs_predicted.png")
    fig.savefig(FIGURES / "actual_vs_predicted_oof.png")
    if "REPORTS_FIGURES" in globals() and REPORTS_FIGURES.exists():
        fig.savefig(REPORTS_FIGURES / "07_actual_vs_predicted_oof.png")
        fig.savefig(REPORTS_FIGURES / "actual_vs_predicted_oof.png")
    if "DASHBOARD_FIGURES" in globals() and DASHBOARD_FIGURES.exists():
        fig.savefig(DASHBOARD_FIGURES / "actual_vs_predicted_oof.png")
    plt.close(fig)


def plot_importance(importance):
    order = np.argsort(importance)[-10:]
    values = importance[order]
    labels = [FEATURES[index].replace("_", " ").title() for index in order]
    fig, axis = plt.subplots(figsize=(7.5, 5), dpi=180)
    axis.barh(labels, values, color="#0f766e")
    axis.axvline(0, color="#64748b", linewidth=0.8)
    axis.set_xlabel("Increase in MAE when permuted")
    axis.set_title("Model Feature Importance (Permutation Impact on Coral Change)")
    axis.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUTPUT / "fig3_feature_importance.png")
    fig.savefig(FIGURES / "feature_importance.png")
    if "REPORTS_FIGURES" in globals() and REPORTS_FIGURES.exists():
        fig.savefig(REPORTS_FIGURES / "08_feature_importance.png")
        fig.savefig(REPORTS_FIGURES / "feature_importance.png")
    if "DASHBOARD_FIGURES" in globals() and DASHBOARD_FIGURES.exists():
        fig.savefig(DASHBOARD_FIGURES / "feature_importance.png")
    plt.close(fig)


def plot_priority_matrix(priority):
    x = priority["predicted_next_change_pct_per_year"].to_numpy()
    y = priority["live_coral_cover_pct"].to_numpy()
    heat_values = priority["noaa_max_dhw"].fill_null(0).to_numpy()
    fig, ax = plt.subplots(figsize=(10, 6), dpi=180)
    points = ax.scatter(x, y, c=heat_values, cmap="OrRd", s=90, edgecolors="#334155")
    ax.axvline(0, color="#64748b", linestyle="--")
    ax.axhline(40, color="#f59e0b", linestyle="--")
    for row in priority.head(10).iter_rows(named=True):
        ax.annotate(row["island"], (row["predicted_next_change_pct_per_year"], row["live_coral_cover_pct"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
    fig.colorbar(points, ax=ax, label="Regional NOAA maximum DHW")
    ax.set_xlabel("Predicted next observed coral-cover change (pp/year)")
    ax.set_ylabel("Current live coral cover (%)")
    ax.set_title("Graph 12: ReefSafe field-verification priority matrix")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUTPUT / "fig6_field_verification_priority_matrix.png")
    fig.savefig(FIGURES / "field_verification_priority_matrix.png")
    if "REPORTS_FIGURES" in globals() and REPORTS_FIGURES.exists():
        fig.savefig(REPORTS_FIGURES / "13_field_verification_priority_matrix.png")
        fig.savefig(REPORTS_FIGURES / "field_verification_priority_matrix.png")
    if "DASHBOARD_FIGURES" in globals() and DASHBOARD_FIGURES.exists():
        fig.savefig(DASHBOARD_FIGURES / "field_verification_priority_matrix.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
