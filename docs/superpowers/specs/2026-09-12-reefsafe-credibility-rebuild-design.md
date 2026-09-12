# ReefSafe Credibility Rebuild Design

## Goal

Turn ReefSafe AI into an auditable early-warning and intervention-prioritisation submission whose data, model, dashboard, report, and video all agree.

## Scope

- Correct NOAA Degree Heating Weeks parsing.
- Remove generated tourism-pressure proxies and use only observed official fields already present in the repository.
- Predict the next observed annualised coral-cover change from information available at the prior survey.
- Compare every model with a simple baseline using forward year splits.
- Describe model evidence as association, not causation.
- Replace the static workbook with an interactive island and policy-priority dashboard driven by the processed dataset.
- Remove unsupported diver caps, asset values, reef-area savings, and causal percentages.
- Regenerate report, PDF, dashboard package, and presentation script from the same outputs.

## Design

`scripts/run_preprocessing.py` owns source parsing and the master dataset. `scripts/train_models.py` owns past-only target construction, validation, metrics, predictions, and figures. The dashboard and report consume those saved outputs without embedding separate analytical numbers.

The product is a screening tool for marine-park officers. It answers which islands need closer inspection, what observed indicators support that priority, how uncertain the model is, and which evidence-based response category applies. It does not claim to calculate legal carrying capacity.

## Verification

One small test module checks the NOAA column mapping, absence of synthetic tourism fields, past-only target alignment, and dashboard interactivity. Final checks rerun preprocessing, modelling, dashboard/report generation, notebook execution, workbook inspection, and visual rendering.
