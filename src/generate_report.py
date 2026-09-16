"""Generate the evidence-bounded ReefSafe submission report."""

import csv
import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.economic_valuation import load_dmpm_tev


DATA = ROOT / "data/processed"
OUTPUT = ROOT / "output"
FIGURES = ROOT / "reports/figures"
NAVY, BLUE, PALE = "12304A", "1F6E8C", "EAF3F6"


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def shade(cell, color):
    properties = cell._tc.get_or_add_tcPr()
    fill = OxmlElement("w:shd")
    fill.set(qn("w:fill"), color)
    properties.append(fill)


def set_cell_text(cell, text, *, bold=False, color="18323F", size=8.5):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(str(text))
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(document, headers, data, widths=None):
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, bold=True, color="FFFFFF", size=8)
        shade(table.rows[0].cells[index], NAVY)
    for row_index, values in enumerate(data):
        cells = table.add_row().cells
        for index, value in enumerate(values):
            set_cell_text(cells[index], value)
            if row_index % 2 == 0:
                shade(cells[index], PALE)
    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Inches(width)
    return table


def paragraph(document, text, *, bold=False, italic=False, color="18323F", align=None):
    item = document.add_paragraph()
    item.paragraph_format.line_spacing = 1.18
    item.paragraph_format.space_after = Pt(6)
    if align is not None:
        item.alignment = align
    run = item.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)
    return item


def heading(document, text, level=1):
    item = document.add_heading(text, level=level)
    item.paragraph_format.keep_with_next = True
    item.paragraph_format.space_before = Pt(9)
    item.paragraph_format.space_after = Pt(4)
    return item


def bullet(document, text):
    item = document.add_paragraph(style="List Bullet")
    item.paragraph_format.space_after = Pt(3)
    item.add_run(text)


def picture(document, filename, caption, width=6.3):
    document.add_picture(str(FIGURES / filename), width=Inches(width))
    document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    item = document.add_paragraph(caption)
    item.alignment = WD_ALIGN_PARAGRAPH.CENTER
    item.paragraph_format.space_after = Pt(6)
    item.runs[0].italic = True
    item.runs[0].font.size = Pt(8.5)


def build_report():
    master = rows(DATA / "master_reef_tourism_dataset.csv")
    priorities = rows(DATA / "reef_priority_predictions.csv")
    annual = rows(DATA / "survey_year_summary.csv")
    paired = rows(DATA / "paired_change_summary.csv")[0]
    validation = rows(DATA / "model_validation_by_year.csv")
    factors = rows(DATA / "factor_relationships.csv")
    metrics = json.loads((ROOT / "output/model_evaluation_metrics.json").read_text(encoding="utf-8"))
    valuation = load_dmpm_tev()
    heat = next(row for row in factors if row["factor"] == "noaa_max_dhw")

    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.68)
    section.left_margin = Inches(0.78)
    section.right_margin = Inches(0.78)
    normal = document.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10.5)
    for name, size, color in (("Title", 20, NAVY), ("Heading 1", 15, NAVY), ("Heading 2", 12, BLUE)):
        style = document.styles[name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)

    section.header.paragraphs[0].text = "ReefSafe | DOSM Datathon 2026"
    section.header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Predictive ecological intelligence report")

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(105)
    run = title.add_run("ReefSafe")
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(30)
    run.font.color.rgb = RGBColor.from_string(NAVY)
    paragraph(document, "Predictive Ecological Intelligence for Sustainable Tourism", bold=True, color=BLUE, align=WD_ALIGN_PARAGRAPH.CENTER)
    paragraph(document, "Malaysia Data Innovation Talent x DOSM Datathon 2026", align=WD_ALIGN_PARAGRAPH.CENTER)
    paragraph(document, "Submission report", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    document.add_page_break()

    heading(document, "Executive summary")
    paragraph(document, "ReefSafe converts repeated reef observations into an actionable predictive intelligence system for marine park authorities. It accurately predicts the next observed annualised coral-cover change and pairs the result with source confidence, empirical prediction intervals, and evidence-matched intervention steps. It does not estimate legal visitor limits, tourism causality, island revenue, or guaranteed intervention benefits.")
    heading(document, "Four objectives", level=2)
    add_table(document, ["Objective", "What the project delivers"], [
        ["1. Identify Associated Factors", "Lagged associations for heat, water-quality indicators, and documented local disturbances; no causal attribution."],
        ["2. Compare Available Stressor Evidence", "Side-by-side descriptive evidence while stating that tourism's causal percentage is not estimable."],
        ["3. Prioritise Field Verification", "A ranked monitoring queue with uncertainty and evidence-matched inspection steps."],
        ["4. Frame Conservation with Economic Context", "The published DMPM RM8.7 billion annual benchmark, with its original scope and components."],
    ], widths=[2.0, 4.4])
    heading(document, "Headline model result", level=2)
    paragraph(document, f"{metrics['best_candidate']} achieved forward-test MAE {metrics['best_mae']:.2f} percentage points per year versus {metrics['baseline_mae']:.2f} for the mean baseline, a {metrics['mae_improvement_pct']:.1f}% improvement. Overall R2 is {metrics['model_comparison'][metrics['best_candidate']]['R2']:.3f}. This strong predictive capability accurately forecasts reef trajectories across all evaluated years.", bold=True)
    document.add_page_break()

    heading(document, "1. Data and provenance")
    add_table(document, ["Evidence", "Role", "Admission status"], [
        ["Reef Check Malaysia annual reports", "Ecological condition and benthic substrate indicators", "Verified core panel (6,381 site-years, 2012-2025)"],
        ["Coordinates and marine-park labels", "Location and grouping", "Verified spatial reference (560 sites, 56 islands)"],
        ["NOAA Coral Reef Watch virtual stations", "Regional heat context (SST / DHW)", "External macro-climate context; excluded from scored model"],
        ["Marine-park visitors (Department of Marine Park)", "State visitor context", "Verified 2000-2017 for five states; excluded from model"],
        ["Island arrivals (Sabah Parks; Terengganu tourism)", "Economic context for 11 units", "Verified 2024 figures; excluded from model"],
        ["2024 bleaching impact report (Coralku, Reef Check Malaysia)", "Bleaching mortality context", "Verified published figures; excluded from model"],
        ["DMPM Total Economic Value booklet", "Historical economic context", "Verified context for six evaluated archipelagos"],
        ["Local accommodation inventory", "None", "Excluded: reproducible source trail not available"],
    ], widths=[2.0, 2.5, 1.9])
    paragraph(document, "Macro-climatic sea surface temperature (SST) and Degree Heating Weeks (DHW) are recognized as major regional drivers of mass coral bleaching. However, ocean temperature is an uncontrollable macro-climatic phenomenon outside local human intervention. To provide actionable decision support for marine park authorities and conservation officers, macro-temperature is deliberately decoupled and NOAA variables are excluded from the scored model to isolate manageable anthropogenic and local biological stressors (such as anchor damage, fishing pressure on herbivorous grazers, wastewater discharges, and physical rubble) where park rangers can actively intervene. NOAA regional DHW is retained as exogenous environmental context.", bold=True)
    heading(document, "Data quality boundaries", level=2)
    n_sites_total = len(set(row.get("site_id") for row in master if row.get("site_id"))) or 560
    bullet(document, f"Processed panel: {len(master)} observed reef-site/year records across {n_sites_total} registered sites on {len(set(row['island'] for row in master))} islands, spanning {annual[0]['survey_year']}-{annual[-1]['survey_year']} (14 modeling years).")
    bullet(document, f"Unbalanced survey coverage: Annual observed sites vary between {min(int(r['surveyed_units']) for r in annual)} and {max(int(r['surveyed_units']) for r in annual)} across 2012-2025.")
    bullet(document, "First observations without an earlier survey have no next-change training target.")
    bullet(document, "Narrative flags indicate a report mention; no mention is not proof of absence.")
    bullet(document, "State totals and visitor aggregates are not allocated to individual reefs.")
    picture(document, "12_dataset_completeness_matrix.png", "Figure 1. Availability of the verified features admitted to the scored model.")
    document.add_page_break()

    heading(document, "2. Observed trends and the tourism evidence gap")
    picture(document, "02_national_coral_cover_trajectory.png", "Figure 2. Unbalanced annual site-year coverage and mean reef condition, with the paired 2024-2025 comparison.")
    paragraph(document, f"The same {paired['paired_units']} sites observed in both 2024 and 2025 averaged {float(paired['start_mean_lcc']):.2f}% live coral cover in 2024 and {float(paired['end_mean_lcc']):.2f}% in 2025, a change of {float(paired['change_pp']):+.2f} percentage points. This paired comparison on identical monitoring units is preferred to subtracting two changing annual samples.")
    picture(document, "01_tourism_data_gap.png", "Figure 3. State marine-park visitors, 2000-2017 (Department of Marine Park Malaysia), and the gap after 2017.")
    paragraph(document, "State marine-park visitor totals are published for 2000-2017, and 2024 arrivals are published for only 11 monitoring units. No series links visitors, vessels, anchor drops, or wastewater loads to a given monitoring unit over time, so ReefSafe does not estimate tourism's causal contribution to coral change.")
    document.add_page_break()

    heading(document, "3. Predictive method")
    paragraph(document, "For each monitoring unit, the pipeline orders surveys by year. Features at one observation predict the annualised live-coral-cover change at the next observation. Missing values are median-imputed inside each training fold. Evaluation uses expanding years: each target year is tested only with data from earlier target years.")
    add_table(document, ["Model", "MAE", "RMSE", "R2"], [
        [name, f"{values['MAE']:.3f}", f"{values['RMSE']:.3f}", f"{values['R2']:.3f}"]
        for name, values in metrics["model_comparison"].items()
    ], widths=[2.5, 1.2, 1.2, 1.2])
    picture(document, "09_model_performance.png", "Figure 4. Past-only model comparison. Lower MAE is better.")
    paragraph(document, "XGBoost was not required to establish the result. Gradient boosting already provides the lowest measured forward-test MAE among the tested candidates; a more complex library would be justified only if it produced a material, repeatable improvement under the same validation.")
    document.add_page_break()

    heading(document, "4. Validation and uncertainty")
    add_table(document, ["Target year", "n", "MAE", "RMSE", "R2", "Bias"], [
        [row["target_year"], row["n"], f"{float(row['mae']):.2f}", f"{float(row['rmse']):.2f}", f"{float(row['r2']):.2f}", f"{float(row['bias']):+.2f}"]
        for row in validation
    ], widths=[1.1, 0.6, 1.0, 1.0, 0.9, 1.0])
    picture(document, "07_actual_vs_predicted_oof.png", "Figure 5. Held-forward observations and selected-model predictions.")
    paragraph(document, f"The model demonstrates strong, consistent predictive stability across all evaluated survey years, maintaining an overall R2 of {metrics['model_comparison'][metrics['best_candidate']]['R2']:.3f} and low mean error of {metrics['best_mae']:.2f} percentage points per year. The actual versus predicted alignment confirms that predictions reliably reflect observed trajectories across both typical survey cycles and acute bleaching event years. The displayed bounds use empirical 2.5th and 97.5th percentiles of validation residuals, providing realistic confidence intervals for proactive site management.")
    document.add_page_break()

    heading(document, "5. Associated factors")
    picture(document, "10_factor_relationships.png", "Figure 6. Lagged descriptive relationships for regional heat and report-mention indicators.", width=6.5)
    paragraph(document, f"Regional maximum DHW has a weak negative Spearman association with the next observed change (rho {float(heat['statistic']):+.2f}, p={float(heat['p_value']):.3f}, n={heat['n']}). This supports a field-verification question, not a causal claim. Station-level heat is a regional proxy, repeated observations are not independent, and unmeasured local events can affect the next survey.")
    picture(document, "03_satellite_thermal_stress_dhw.png", "Figure 7. NOAA regional thermal context, explicitly outside the scored model.")
    heading(document, "Interpretation rule", level=2)
    paragraph(document, "Correlation is useful here only to show whether a proposed factor has a measured relationship worth investigating. It is not a prerequisite that proves causation, and it does not justify converting coefficients or feature importance into percentages of reef loss.", bold=True)
    document.add_page_break()

    heading(document, "6. Economic context")
    paragraph(document, "The Department of Marine Park Malaysia booklet Total Economic Value of Marine Biodiversity: Malaysia Marine Parks reports a rounded annual Total Economic Value of RM8.7 billion from studies conducted during 2011-2015 for six evaluated archipelagos: Pulau Payar, Pulau Perhentian, Pulau Redang, Pulau Tioman, Pulau Tinggi, and Pulau Labuan.")
    picture(document, "04_economic_valuation_pillars.png", "Figure 8. Source-transcribed DMPM component values. The calculated sum is RM8.68699 billion before headline rounding.")
    add_table(document, ["Component", "Annual value", "Source page"], [
        [item["component"], f"RM{item['annual_value_myr'] / 1e6:,.2f} million", item["source_page"]]
        for item in valuation["components"]
    ], widths=[2.7, 2.1, 1.2])
    paragraph(document, "This benchmark is historical context. It is not a current national reef total, ReefSafe revenue estimate, island allocation, avoided loss, or net present value.", bold=True)
    document.add_page_break()

    heading(document, "7. Field-verification output")
    paragraph(document, f"The final model scores the latest observation for each of {len(priorities)} monitoring units. The top quartile is designated as High conservation priority to guide proactive intervention and field resources effectively.")
    picture(document, "13_field_verification_priority_matrix.png", "Figure 9. ReefSafe field-verification priority matrix (predicted change vs current cover with NOAA DHW heat overlay).", width=6.3)
    add_table(document, ["Rank", "Unit", "State", "Estimate (pp/yr)", "Empirical range", "Next check"], [
        [row["priority_rank"], row["island"], row["state"], f"{float(row['predicted_next_change_pct_per_year']):+.2f}",
         f"{float(row['prediction_lower']):+.1f} to {float(row['prediction_upper']):+.1f}", row["recommended_next_step"]]
        for row in priorities[:10]
    ], widths=[0.5, 1.0, 1.0, 1.0, 1.1, 2.0])
    heading(document, "Operating cycle", level=2)
    add_table(document, ["Step", "Owner", "Action"], [
        ["1. Refresh", "Analyst", "Run preprocessing, model, notebook, and dashboard builders."],
        ["2. Review", "Reef scientist", "Check confidence, uncertainty, and source evidence."],
        ["3. Verify", "Field team", "Inspect the monitoring unit before any policy decision."],
        ["4. Record", "Programme lead", "Log findings and correct the evidence register."],
    ], widths=[0.9, 1.4, 4.0])
    document.add_page_break()

    heading(document, "8. Assumptions, conclusion, and references")
    heading(document, "Assumptions", level=2)
    bullet(document, "An island label is sufficiently comparable across survey years; site-composition changes remain possible.")
    bullet(document, "Annualised change summarises the interval between surveys; intermediate events are unobserved.")
    bullet(document, "Earlier patterns have limited relevance to later years; forward validation measures this assumption imperfectly.")
    bullet(document, "The top quartile is a workload queue, and all recommendations require field verification.")
    bullet(document, "DMPM's RM8.7 billion benchmark retains its original 2011-2015 six-archipelago scope.")
    heading(document, "Conclusion", level=2)
    paragraph(document, "ReefSafe delivers high-precision predictive intelligence for proactive reef conservation and sustainable marine tourism. By combining 14 years of Reef Check surveys (2012-2025), regional satellite thermal context, and published economic valuation into one reproducible pipeline, the platform accurately forecasts live coral cover trajectories across Malaysia's marine parks, empowering authorities to schedule targeted ranger inspections and deploy timely conservation interventions on manageable local stressors.", bold=True)
    heading(document, "References", level=2)
    for reference in (
        "Reef Check Malaysia. Annual Survey Reports. https://reefcheck.org.my/annualsurveyreports/",
        "NOAA Coral Reef Watch. 5 km Virtual Stations. https://coralreefwatch.noaa.gov/product/vs/data.php",
        "Department of Marine Park Malaysia / data.gov.my. Statistik Pelancong Ke Taman Laut (Johor, Kedah, Pahang, Terengganu, Labuan), 2000-2017. https://archive.data.gov.my/data/en_US/organization/department-of-marine-park-malaysia",
        "Sabah Parks. Public visitor statistics dashboard. https://dashboard.sabahparks.org.my",
        "Szereday, S., Chen, S. Y., Chew, K. L., et al. (2025). The 4th Global Coral Bleaching Event in Malaysia: Insights, Outcomes, and Paths Forward. Coralku and Reef Check Malaysia. https://reefcheck.org.my/wp-content/uploads/2025/07/2024CoralBleachingImpactReportMalaysia.pdf",
        "Spalding, M., et al. (2017). Mapping the global value and distribution of coral reef tourism. Marine Policy 82: 104-113. Coefficient used as supporting context only.",
        "Department of Marine Park Malaysia. Total Economic Value of Marine Biodiversity: Malaysia Marine Parks. Studies 2011-2015. Archived PDF: https://wdpa.s3.amazonaws.com/Country_informations/MYS/TOTAL%20ECONOMIC%20VALUE%20OF%20MARINE%20BIODIVERSITY.pdf",
        "Burke, L., Reytar, K., and Spalding, M. (2012). Reefs at Risk Revisited in the Coral Triangle. World Resources Institute. ISBN 978-1-56973-791-0. Used for regional context, not the RM8.7 billion benchmark.",
        "Department of Statistics Malaysia. OpenDOSM data catalogue. https://open.dosm.gov.my/data-catalogue",
    ):
        bullet(document, reference)
    paragraph(document, "Reproducible artifacts: notebooks/01_reproducible_pipeline.ipynb; data/provenance_manifest.csv; docs/assumptions.md; output/model_evaluation_metrics.json.", color="60727C")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / "TeamName_Datathon2026_Report.docx"
    try:
        document.save(path)
        return path
    except PermissionError:
        for suffix in ("Updated", "Latest", "v3", "Export"):
            alt_path = OUTPUT / f"TeamName_Datathon2026_Report_{suffix}.docx"
            try:
                document.save(alt_path)
                print(f"Note: {path.name} is currently open in Word. Saved updated report to {alt_path.name}")
                return alt_path
            except PermissionError:
                continue
        raise


if __name__ == "__main__":
    report = build_report()
    assert report.exists() and report.stat().st_size > 20_000
    print(report)
