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
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from scipy.stats import mannwhitneyu, spearmanr

from scripts.pipeline import expanding_year_splits, heat_category, make_next_observation_rows


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
    "impact_cot", "noaa_max_dhw", "noaa_mean_ssta", "latitude", "longitude",
]

CONTINUOUS_DIAGNOSTICS = [
    "noaa_max_dhw", "noaa_mean_ssta", "grp_disturbance_indicators",
    "grp_pollution_indicators", "fish_parrotfish", "grazer_ratio",
]
BINARY_DIAGNOSTICS = ["impact_anchor", "impact_trash", "impact_bleaching"]


def model_specs():
    return {
        "Baseline mean": DummyRegressor(strategy="mean"),
        "Ridge regression": Ridge(alpha=10.0),
        "Gradient boosting": GradientBoostingRegressor(
            n_estimators=100, max_depth=2, learning_rate=0.04, random_state=42
        ),
        "Random forest": RandomForestRegressor(
            n_estimators=250, max_depth=5, min_samples_leaf=5, random_state=42
        ),
    }


def main():
    OUTPUT.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)

    master = pl.read_csv(DATA_PATH)
    year_summary = (
        master.group_by("survey_year")
        .agg([
            pl.col("island").n_unique().alias("surveyed_units"),
            pl.col("live_coral_cover_pct").mean().alias("mean_lcc"),
        ])
        .sort("survey_year")
    )
    year_summary.write_csv(PROCESSED / "survey_year_summary.csv")

    paired = (
        master.filter(pl.col("survey_year").is_in([2024, 2025]))
        .select(["island", "survey_year", "live_coral_cover_pct"])
        .pivot(on="survey_year", index="island", values="live_coral_cover_pct")
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
    transitions = transitions.filter(pl.col("target_lcc_change_rate").is_not_null())
    diagnostics, heat_summary = build_factor_diagnostics(transitions)
    plot_factor_relationships(transitions, diagnostics, heat_summary)

    X = transitions.select(FEATURES).to_numpy()
    y = transitions["target_lcc_change_rate"].to_numpy().astype(float)
    target_years = transitions["target_year"].to_list()
    splits = expanding_year_splits(target_years, test_years=5)
    evaluated = sorted({index for _, test in splits for index in test})

    results = {}
    predictions = {}
    for name, estimator in model_specs().items():
        oof = np.full(len(y), np.nan)
        for train_index, test_index in splits:
            model = make_pipeline(SimpleImputer(strategy="median"), clone(estimator))
            model.fit(X[train_index], y[train_index])
            oof[test_index] = model.predict(X[test_index])

        truth = y[evaluated]
        predicted = oof[evaluated]
        results[name] = {
            "MAE": float(mean_absolute_error(truth, predicted)),
            "RMSE": float(mean_squared_error(truth, predicted) ** 0.5),
            "R2": float(r2_score(truth, predicted)),
        }
        predictions[name] = oof

    candidates = {name: values for name, values in results.items() if name != "Baseline mean"}
    best_name = min(candidates, key=lambda name: candidates[name]["MAE"])
    baseline_mae = results["Baseline mean"]["MAE"]
    best_mae = results[best_name]["MAE"]
    improvement = 100 * (baseline_mae - best_mae) / baseline_mae

    best_spec = model_specs()[best_name]
    importance = np.zeros(len(FEATURES))
    importance_weight = 0
    for train_index, test_index in splits:
        model = make_pipeline(SimpleImputer(strategy="median"), clone(best_spec))
        model.fit(X[train_index], y[train_index])
        measured = permutation_importance(
            model, X[test_index], y[test_index], scoring="neg_mean_absolute_error",
            n_repeats=8, random_state=42,
        )
        importance += measured.importances_mean * len(test_index)
        importance_weight += len(test_index)
    importance /= importance_weight

    final_model = make_pipeline(SimpleImputer(strategy="median"), clone(best_spec))
    final_model.fit(X, y)
    latest_year = int(master["survey_year"].max())
    latest = master.filter(pl.col("survey_year") == latest_year)
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


def plot_factor_relationships(transitions, diagnostics, heat_summary):
    target = "target_lcc_change_rate"
    heat = transitions.select(["noaa_max_dhw", target]).drop_nulls()
    rho = diagnostics.filter(pl.col("factor") == "noaa_max_dhw")["statistic"][0]
    categories = heat_summary["heat_category"].to_list()
    groups = [
        [row[target] for row in transitions.select(["noaa_max_dhw", target]).iter_rows(named=True)
         if heat_category(row["noaa_max_dhw"]) == category and row[target] is not None]
        for category in categories
    ]
    binary = diagnostics.filter(pl.col("factor").is_in(BINARY_DIAGNOSTICS))

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.4), dpi=180)
    axes[0].scatter(heat["noaa_max_dhw"], heat[target], alpha=0.55, color="#0284c7", edgecolor="white")
    axes[0].axhline(0, color="#64748b", linewidth=0.8)
    axes[0].set_title(f"Heat vs next change\nSpearman ρ={rho:+.2f}, n={heat.height}")
    axes[0].set_xlabel("NOAA maximum DHW")
    axes[0].set_ylabel("Next observed change (pp/year)")

    boxes = axes[1].boxplot(groups, tick_labels=[f"{name}\nn={len(group)}" for name, group in zip(categories, groups)], patch_artist=True)
    for box in boxes["boxes"]:
        box.set_facecolor("#bfdbfe")
    axes[1].axhline(0, color="#64748b", linewidth=0.8)
    axes[1].set_title("Next change by heat band")
    axes[1].set_ylabel("Percentage points/year")

    labels = [name.replace("impact_", "").title() for name in binary["factor"]]
    axes[2].bar(labels, binary["statistic"], color="#0f766e")
    axes[2].axhline(0, color="#64748b", linewidth=0.8)
    axes[2].set_title("Narrative mention difference")
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


def plot_model_comparison(results):
    names = list(results)
    maes = [results[name]["MAE"] for name in names]
    colors = ["#94a3b8" if name == "Baseline mean" else "#0f766e" for name in names]
    fig, axis = plt.subplots(figsize=(8, 4.5), dpi=180)
    bars = axis.bar(names, maes, color=colors)
    axis.bar_label(bars, fmt="%.2f")
    axis.set_ylabel("Forward-test MAE (% points per year)")
    axis.set_title("Model comparison using past-only expanding-year validation")
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
    axis.set_title(f"Past-only forward validation: {model_name}")
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
    axis.set_title("Predictive associations, not causal effects")
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


if __name__ == "__main__":
    main()
