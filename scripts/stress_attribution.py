"""Split each monitoring unit's prediction into factor-group contributions.

The selected model is a scikit-learn GradientBoostingRegressor behind a median
SimpleImputer. Its prediction for one row decomposes exactly into a baseline plus
one contribution per feature by tracing the row's path through every tree and
crediting each split's change in node value to the split feature (Saabas 2014,
"Interpreting random forests"). Contributions are grouped into factor groups and
reported in percentage points per year. They describe the model, not causes.
"""

import numpy as np

# Every production feature belongs to exactly one group.
FACTOR_GROUPS = {
    "Starting condition & trend": ["live_coral_cover_pct", "lcc_change_rate", "island_vs_region_pct"],
    "Herbivory & fish": ["fish_parrotfish", "fish_butterflyfish", "fish_snapper", "fish_grouper",
                         "inv_diadema_urchin", "grazer_ratio"],
    "Anchors & nets": ["impact_anchor", "impact_nets"],
    "Pollution & waste": ["grp_pollution_indicators", "impact_trash"],
    "Disturbance & substrate": ["grp_disturbance_indicators", "grp_available_substrate", "grp_sand"],
    "Crown-of-thorns": ["inv_crown_of_thorns", "impact_cot"],
    "Bleaching reported": ["impact_bleaching"],
    "Region & survey year": ["latitude", "longitude", "survey_year"],
}

# Groups that describe a pressure on the reef; the other two are context.
STRESSOR_GROUPS = [
    "Herbivory & fish", "Anchors & nets", "Pollution & waste",
    "Disturbance & substrate", "Crown-of-thorns", "Bleaching reported",
]

# A stressor is named only if it pushes the prediction at least this far towards decline.
MIN_STRESSOR_PUSH_PP = 0.25

# Plain labels and value kinds for the stressor inputs (Reef Check Malaysia data dictionary):
# pct = % of substrate, count = individuals per 100 m², ratio, flag = 0/1 report mention.
FEATURE_INFO = {
    "fish_parrotfish": ("Parrotfish", "count"),
    "fish_butterflyfish": ("Butterflyfish", "count"),
    "fish_snapper": ("Snapper", "count"),
    "fish_grouper": ("Grouper", "count"),
    "inv_diadema_urchin": ("Diadema urchins", "count"),
    "grazer_ratio": ("Grazer ratio (parrotfish ÷ urchins)", "ratio"),
    "impact_anchor": ("Anchor damage mentioned", "flag"),
    "impact_nets": ("Discarded nets mentioned", "flag"),
    "grp_pollution_indicators": ("Pollution indicators (nutrient algae + silt)", "pct"),
    "impact_trash": ("Trash mentioned", "flag"),
    "grp_disturbance_indicators": ("Disturbance indicators (recently killed coral + rubble)", "pct"),
    "grp_available_substrate": ("Bare rock available for coral recruitment", "pct"),
    "grp_sand": ("Sand", "pct"),
    "inv_crown_of_thorns": ("Crown-of-thorns starfish", "count"),
    "impact_cot": ("Crown-of-thorns mentioned", "flag"),
    "impact_bleaching": ("Bleaching mentioned", "flag"),
}

GROUP_NOTES = {
    "Herbivory & fish": "Counts are individuals per 100 m²; a low grazer ratio means urchins, not fish, do most of the grazing.",
    "Anchors & nets": "Flags record a mention in the Reef Check report, not severity.",
    "Pollution & waste": "Pollution indicators combine nutrient algae and silt; the trash flag is a report mention, not severity.",
    "Disturbance & substrate": "Recently killed coral and rubble signal physical damage such as anchors, trampling, storms or blasting.",
    "Crown-of-thorns": "Outbreak level is roughly 0.2–0.3 starfish per 100 m²; the flag is a report mention.",
    "Bleaching reported": "A mention in the Reef Check report, not a severity measure.",
}

# The report's evidence rule (reef_priority_predictions.csv) mapped to a factor group and action.
REPORT_STRESSORS = {
    "NOAA thermal stress observed": ("Bleaching reported", "Coordinate targeted bleaching survey"),
    "Anchor impact mentioned in Reef Check report": ("Anchors & nets", "Inspect mooring & anchoring controls"),
    "Waste or pollution indicator is elevated": ("Pollution & waste", "Inspect waste and wastewater controls"),
    "Modelled decline; no single dominant observed stressor": (None, "Prioritise field validation before restrictions"),
}

INSIGHTS = {
    "Herbivory & fish": "Review fishing pressure on grazing fish",
    "Anchors & nets": "Check mooring buoys and anchoring controls",
    "Pollution & waste": "Inspect wastewater and waste controls",
    "Disturbance & substrate": "Survey physical reef damage",
    "Crown-of-thorns": "Survey and remove crown-of-thorns starfish",
    "Bleaching reported": "Coordinate a bleaching survey",
    None: "No measured stressor drives this prediction; verify in the field before acting",
}


def tree_path_contributions(pipeline, X):
    """Return (baseline, contributions) for rows X, where contributions has one column
    per feature and baseline + contributions.sum(axis=1) equals pipeline.predict(X)."""
    imputer = pipeline.named_steps["simpleimputer"]
    model = pipeline.named_steps["gradientboostingregressor"]
    rows = imputer.transform(X).astype(np.float32)
    baseline = float(model.init_.predict(rows[:1])[0])
    contributions = np.zeros(rows.shape)
    for tree in model.estimators_[:, 0]:
        structure = tree.tree_
        for index, row in enumerate(rows):
            node = 0
            while structure.children_left[node] != -1:
                feature = structure.feature[node]
                if row[feature] <= structure.threshold[node]:
                    child = structure.children_left[node]
                else:
                    child = structure.children_right[node]
                contributions[index, feature] += model.learning_rate * (
                    structure.value[child][0][0] - structure.value[node][0][0])
                node = child
    return baseline, contributions


def group_contributions(feature_names, contribution_row):
    """Sum one row of feature contributions into the factor groups, in group order."""
    position = {name: index for index, name in enumerate(feature_names)}
    return {group: float(sum(contribution_row[position[name]] for name in names))
            for group, names in FACTOR_GROUPS.items()}


def strongest_stressor(groups):
    """The stressor group pushing hardest towards decline at any size, or (None, 0.0) if none pushes down."""
    group, push = min(((name, groups[name]) for name in STRESSOR_GROUPS), key=lambda item: item[1])
    return (group, push) if push < 0 else (None, 0.0)


def top_stressor(groups):
    """The stressor group pushing hardest towards decline, or None if none passes the threshold."""
    group, push = strongest_stressor(groups)
    return (group, push) if push <= -MIN_STRESSOR_PUSH_PP else (None, 0.0)
