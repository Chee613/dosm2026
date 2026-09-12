from __future__ import annotations

import csv
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUTPUT = ROOT / "output"
NAVY, BLUE, PALE, RED, GREEN = "12304A", "1F6E8C", "EAF3F6", "FCE8E6", "E2F0D9"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def shade(cell, color: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    fill = properties.find(qn("w:shd"))
    if fill is None:
        fill = OxmlElement("w:shd")
        properties.append(fill)
    fill.set(qn("w:fill"), color)


def set_cell_text(cell, text: str, *, bold=False, color="18323F", size=9) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(str(text))
    run.bold = bold
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(doc: Document, headers: list[str], data: list[list[object]], widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = widths is None
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, bold=True, color="FFFFFF", size=9)
        shade(table.rows[0].cells[index], NAVY)
        if widths:
            table.rows[0].cells[index].width = Inches(widths[index])
    for row_index, values in enumerate(data):
        cells = table.add_row().cells
        for index, value in enumerate(values):
            set_cell_text(cells[index], value, size=8.5)
            if row_index % 2 == 0:
                shade(cells[index], PALE)
            if widths:
                cells[index].width = Inches(widths[index])
    return table


def add_field(paragraph, instruction: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    code = OxmlElement("w:instrText")
    code.set(qn("xml:space"), "preserve")
    code.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, code, separate, end])


def paragraph(doc: Document, text: str, *, bold=False, italic=False, color="18323F", align=None):
    item = doc.add_paragraph()
    item.paragraph_format.line_spacing = 1.5
    item.paragraph_format.space_after = Pt(7)
    if align is not None:
        item.alignment = align
    run = item.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)
    return item


def heading(doc: Document, text: str, level=1):
    item = doc.add_heading(text, level=level)
    item.paragraph_format.keep_with_next = True
    item.paragraph_format.space_before = Pt(10)
    item.paragraph_format.space_after = Pt(5)
    return item


def bullet(doc: Document, text: str):
    item = doc.add_paragraph(style="List Bullet")
    item.paragraph_format.line_spacing = 1.5
    item.paragraph_format.space_after = Pt(4)
    item.add_run(text)
    return item


def picture(doc: Document, path: Path, caption: str, width=6.2):
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap = doc.add_paragraph(caption)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(8)
    cap.runs[0].italic = True
    cap.runs[0].font.size = Pt(9)


def build_report() -> Path:
    master = rows(DATA / "master_reef_tourism_dataset.csv")
    predictions = rows(DATA / "reef_priority_predictions.csv")
    metrics = rows(DATA / "model_evaluation_metrics.csv")
    factors = rows(DATA / "factor_relationships.csv")
    heat_bands = rows(DATA / "heat_category_summary.csv")
    years = sorted({int(row["survey_year"]) for row in master})
    islands = {row["island"] for row in master}
    baseline = next(row for row in metrics if row["Model"] == "Baseline mean")
    best = min((row for row in metrics if row["Model"] != "Baseline mean"), key=lambda row: float(row["MAE (%/yr)"]))
    improvement = 1 - float(best["MAE (%/yr)"]) / float(baseline["MAE (%/yr)"])
    heat_factor = next(row for row in factors if row["factor"] == "noaa_max_dhw")
    low_heat = next(row for row in heat_bands if row["heat_category"] == "DHW < 1")
    high_heat = next(row for row in heat_bands if row["heat_category"] == "DHW ≥ 4")
    annual: dict[int, list[float]] = {}
    for row in master:
        annual.setdefault(int(row["survey_year"]), []).append(float(row["live_coral_cover_pct"]))
    mean_start = sum(annual[years[0]]) / len(annual[years[0]])
    mean_end = sum(annual[years[-1]]) / len(annual[years[-1]])

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    for name, size, color in [("Title", 20, NAVY), ("Heading 1", 15, NAVY), ("Heading 2", 13, BLUE)]:
        style = styles[name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)

    header = section.header.paragraphs[0]
    header.text = "ReefSafe | DOSM Datathon 2026"
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header.runs[0].font.size = Pt(9)
    header.runs[0].font.color.rgb = RGBColor.from_string(BLUE)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Page ")
    add_field(footer, "PAGE")

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(100)
    run = title.add_run("ReefSafe")
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(30)
    run.font.color.rgb = RGBColor.from_string(NAVY)
    subtitle = paragraph(doc, "Evidence-led reef screening for sustainable tourism management", bold=True, color=BLUE, align=WD_ALIGN_PARAGRAPH.CENTER)
    subtitle.paragraph_format.space_after = Pt(24)
    paragraph(doc, "Malaysia Data Innovation Talent × DOSM Datathon 2026", align=WD_ALIGN_PARAGRAPH.CENTER)
    paragraph(doc, "Theme: Machine Learning and Artificial Intelligence for Sustainable Tourism", italic=True, color="60727C", align=WD_ALIGN_PARAGRAPH.CENTER)
    paragraph(doc, "Submission report", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_page_break()

    heading(doc, "Executive summary")
    paragraph(doc, "ReefSafe is a screening system for marine-park teams. It combines long-running reef observations with NOAA thermal-stress records to identify islands that merit earlier field checks. It does not calculate legal visitor caps, estimate tourism revenue at island level, or prove that tourism caused a change in coral cover.")
    add_table(doc, ["Evidence base", "Coverage", "Decision output"], [[f"{len(master)} observed island-years", f"{len(islands)} islands, {years[0]}–{years[-1]}", "Ranked field-check priority"], ["Past-only model evaluation", "183 held-forward observations", "Prediction band + uncertainty"], ["Observed stressor flags", "Thermal, anchor, waste/pollution", "Evidence-matched next step"]], widths=[2.1, 2.1, 2.1])
    heading(doc, "What changed after validation", level=2)
    bullet(doc, "Removed fabricated island-level tourism pressure and GDP-intensity variables.")
    bullet(doc, "Corrected NOAA Degree Heating Weeks parsing and preserved missing values as missing.")
    bullet(doc, "Changed the target from same-row reconstruction to the next observed coral-cover change.")
    bullet(doc, "Replaced random/group folds with expanding-year evaluation so training always precedes testing.")
    bullet(doc, "Downgraded claims to screening-only because predictive gain is modest and causality is not identified.")
    heading(doc, "Headline result", level=2)
    paragraph(doc, f"The selected Gradient Boosting model recorded MAE {float(best['MAE (%/yr)']):.2f} percentage points per year versus {float(baseline['MAE (%/yr)']):.2f} for the mean baseline—an improvement of {improvement:.1%}. Its forward-test R² was {float(best['R2 Score']):.3f}. This is enough for a cautious triage aid, not enough for automated enforcement.", bold=True)
    doc.add_page_break()

    heading(doc, "1. Decision problem")
    paragraph(doc, "Marine managers must decide where limited inspection, bleaching response, mooring checks, and waste-control resources should go first. National tourism totals are useful for context but cannot be credibly assigned to individual islands without island-level visitor-flow data. ReefSafe therefore focuses on the decision that the available evidence can support: which monitored islands require closer verification, and why?")
    heading(doc, "1.1 Intended users and use")
    add_table(doc, ["User", "Decision", "ReefSafe support"], [["Marine-park officer", "Schedule field checks", "Priority rank, evidence, uncertainty"], ["Reef scientist", "Coordinate follow-up survey", "Observed LCC, thermal stress, data confidence"], ["Policy team", "Allocate monitoring resources", "National trend and transparent model benchmark"]], widths=[1.6, 2.1, 2.7])
    heading(doc, "1.2 Guardrails")
    bullet(doc, "No island-level tourism values are inferred from state totals.")
    bullet(doc, "Feature importance is described as association, not cause.")
    bullet(doc, "A high rank triggers verification; it is not a closure order or carrying-capacity quota.")
    bullet(doc, "Thermal evidence never becomes a claim that visitors caused bleaching.")
    heading(doc, "1.3 Observed national context")
    paragraph(doc, f"The unweighted mean live coral cover among surveyed island observations was {mean_start:.1f}% in {years[0]} and {mean_end:.1f}% in {years[-1]}. Survey composition changes across years, so this descriptive line should not be read as a fixed-panel national estimate.")
    doc.add_page_break()

    heading(doc, "2. Data and provenance")
    add_table(doc, ["Source", "Role", "Treatment"], [["Reef Check Malaysia annual reports", "Island-year coral, substrate, fish, invertebrate and narrative indicators", "Primary ecological evidence; confidence field retained"], ["NOAA Coral Reef Watch", "Sea-surface temperature anomaly and Degree Heating Weeks", "Matched to regional stations; missing remains blank"], ["OpenDOSM tourism and GDP series", "National/state descriptive context", "Not downscaled into model features"], ["DOSM Datathon 2026 booklet", "Submission and evidence rules", "No simulated or fabricated observations"]], widths=[1.7, 2.8, 2.0])
    heading(doc, "2.1 Data quality controls")
    bullet(doc, "404 processed island-year rows and 46 retained fields.")
    bullet(doc, "NOAA rows use the published DHW field, not the adjacent threshold-exceedance field.")
    bullet(doc, "Coordinates, marine-park labels, source confidence, and extraction source are retained for audit.")
    bullet(doc, "First observations without a previous survey have no change-rate target and are excluded from transition modeling.")
    heading(doc, "2.2 Known evidence limitations")
    paragraph(doc, "Survey coverage is uneven across islands and years. Narrative impact flags indicate that a stressor was mentioned in a report; they are not continuous measurements of intensity. Regional NOAA stations do not replace in-water temperature loggers. Results should be refreshed whenever extraction corrections or new survey years become available.")
    doc.add_page_break()

    heading(doc, "3. Modeling method")
    paragraph(doc, "Each training example uses conditions recorded for an island at one survey and predicts the annualized live-coral-cover change observed at that island's next survey. Rows are ordered within island before the target is created. Evaluation uses the latest five target years as separate test periods; every test year is trained only on earlier target years.")
    heading(doc, "3.1 Compared models")
    add_table(doc, ["Model", "MAE (pp/yr)", "RMSE (pp/yr)", "R²"], [[row["Model"], f"{float(row['MAE (%/yr)']):.3f}", f"{float(row['RMSE (%/yr)']):.3f}", f"{float(row['R2 Score']):.3f}"] for row in metrics], widths=[2.4, 1.3, 1.3, 1.0])
    heading(doc, "3.2 Model selection")
    paragraph(doc, f"Gradient Boosting had the lowest forward-test MAE ({float(best['MAE (%/yr)']):.3f} pp/yr). The difference from the baseline is only {improvement:.1%}; therefore the model is retained only for relative screening. The dashboard keeps the baseline comparison and R² visible so users cannot mistake the ranking for high-accuracy forecasting.")
    picture(doc, ROOT / "output" / "fig1_model_performance_cv.png", "Figure 1. Forward-test model comparison. Lower MAE and RMSE are better.", width=6.0)
    doc.add_page_break()

    heading(doc, "4. Results and interpretation")
    picture(doc, ROOT / "output" / "fig2_actual_vs_predicted.png", "Figure 2. Held-forward observations versus predictions for the selected model.", width=6.0)
    paragraph(doc, "Predictions remain concentrated around the centre of the observed distribution and do not reproduce extreme annual changes well. Wide empirical prediction bands are shown in the dashboard. This behaviour is consistent with the low positive R² and reinforces the need for field verification.")
    picture(doc, ROOT / "output" / "fig3_feature_importance.png", "Figure 3. Forward-test permutation importance. Values indicate predictive association, not causation.", width=6.0)
    doc.add_page_break()

    heading(doc, "4.1 Factor relationships")
    picture(doc, ROOT / "output" / "fig4_factor_relationships.png", "Figure 4. Factors measured at the current observation versus the next observed coral-cover change. These are descriptive lagged associations, not causal effects.", width=6.5)
    paragraph(doc, f"Maximum NOAA DHW had a weak negative Spearman relationship with the next observed coral-cover change (rho {float(heat_factor['statistic']):+.3f}, p={float(heat_factor['p_value']):.3f}, n={heat_factor['n']}). The mean next change was {float(low_heat['mean_next_change_pp_per_year']):+.2f} pp/year for DHW below 1 and {float(high_heat['mean_next_change_pp_per_year']):+.2f} pp/year for DHW at least 4. This pattern is directionally consistent with heat stress, but the regional station match, irregular surveys, repeated islands and unmeasured local events prevent causal interpretation.")
    paragraph(doc, "Narrative anchor, trash and bleaching flags did not show strong group separation in this sample. Absence of a narrative mention is not confirmed absence, so these indicators remain evidence prompts rather than causal or predictive conclusions.")
    doc.add_page_break()

    heading(doc, "5. Priority output")
    paragraph(doc, "The latest available record for each island is scored by the final model. The top quartile is labelled ‘High screening priority’; all other islands remain in ‘Monitor’. Evidence and recommended actions are rule-based and intentionally conservative.")
    add_table(doc, ["Rank", "Island", "State", "Prediction", "Observed evidence", "Next step"], [[row["priority_rank"], row["island"], row["state"], f"{float(row['predicted_next_change_pct_per_year']):.1f}", row["evidence"], row["recommended_next_step"]] for row in predictions[:10]], widths=[0.45, 1.0, 0.75, 0.75, 1.5, 1.8])
    heading(doc, "5.1 Evidence-to-action rules", level=2)
    bullet(doc, "DHW ≥ 4: coordinate bleaching assessment; do not attribute heat-driven loss to visitors.")
    bullet(doc, "Anchor impact mentioned: inspect mooring availability and anchoring controls.")
    bullet(doc, "Waste/pollution indicator elevated: inspect waste and wastewater controls.")
    bullet(doc, "No dominant observed stressor: prioritise field validation before restrictions.")
    doc.add_page_break()

    heading(doc, "6. Dashboard and operating workflow")
    picture(doc, ROOT / "dist" / "dashboard_package" / "audit" / "Dashboard.png", "Figure 5. Interactive Excel dashboard. The yellow island selector drives formula-linked evidence and actions.", width=6.6)
    heading(doc, "6.1 Recommended operating cycle", level=2)
    add_table(doc, ["Step", "Owner", "Action"], [["1. Refresh", "Data analyst", "Run preprocessing and model scripts after new reports arrive"], ["2. Review", "Reef scientist", "Check source confidence, uncertainty, and observed stressors"], ["3. Verify", "Marine-park team", "Conduct targeted field checks before enforcement"], ["4. Record", "Programme lead", "Log action, outcome, and corrected evidence for the next cycle"]], widths=[0.9, 1.5, 4.0])
    doc.add_page_break()

    heading(doc, "7. Limitations, next data, and conclusion")
    heading(doc, "7.1 Limitations", level=2)
    bullet(doc, "The evaluation sample is small and temporally irregular; several island histories are sparse.")
    bullet(doc, "The model's 1.5% MAE gain and R² 0.051 are weak; rank stability should be monitored after each refresh.")
    bullet(doc, "No island-level visitor count, vessel movement, wastewater load, enforcement, or revenue series is available in the modeled table.")
    bullet(doc, "Prediction bands are empirical and should not be treated as formal confidence intervals for policy liability.")
    heading(doc, "7.2 Project assumptions", level=2)
    add_table(doc, ["Assumption", "Risk", "Mitigation"], [["Island names represent comparable monitoring units", "Site composition may change", "Retain source confidence and verify large movements"], ["Live coral cover is sufficiently comparable across reports", "Method or observer changes may affect values", "Use results for screening only"], ["Annualized change is approximately linear between surveys", "Intermediate disturbance and recovery are unseen", "Keep survey and target years explicit"], ["NOAA regional station represents broad heat exposure", "Local reef temperature can differ", "Request in-water confirmation"], ["No narrative mention is uncertain absence", "Reporting intensity varies", "Treat flags as evidence prompts"], ["The top quartile is a workload queue", "It is not a scientific threshold", "Require field verification"]], widths=[2.2, 2.0, 2.2])
    paragraph(doc, "The full assumption register is maintained in docs/assumptions.md. OpenDOSM state and national totals are explicitly not assumed to measure individual-island tourism pressure.", color="60727C")
    heading(doc, "7.3 Highest-value next data", level=2)
    paragraph(doc, "The most useful enhancement is not a larger algorithm. It is island-level operational data: daily visitors, boat trips, mooring use, wastewater discharge, closures, bleaching observations, and consistent site-level survey identifiers. Those measurements would allow explicit pressure-response analysis and later testing of intervention effects.")
    heading(doc, "7.4 Conclusion", level=2)
    paragraph(doc, "ReefSafe turns heterogeneous public evidence into a transparent queue for field verification. Its professional value lies in traceability and restraint: the dashboard shows what is observed, what is predicted, how uncertain the prediction is, and what claim the data cannot support.", bold=True)
    heading(doc, "References and reproducibility", level=2)
    paragraph(doc, "Primary evidence: Reef Check Malaysia annual survey reports; NOAA Coral Reef Watch station time series; OpenDOSM structured tourism/GDP files; DOSM Datathon 2026 booklet. Reproducible commands and packaged source files are listed in the repository README and dashboard-package README. Processed data: data/processed/master_reef_tourism_dataset.csv. Evaluation: data/processed/model_evaluation_metrics.csv. Diagnostics: data/processed/factor_relationships.csv and heat_category_summary.csv.", color="60727C")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / "TeamName_Datathon2026_Report.docx"
    doc.save(path)
    return path


if __name__ == "__main__":
    report = build_report()
    assert report.exists() and report.stat().st_size > 20_000
    print(report)
