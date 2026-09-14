import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DATA = path.join(ROOT, "data", "processed");
const OUT = path.join(ROOT, "dist", "dashboard_package");
const AUDIT = path.join(OUT, "audit");
const XLSX_PATH = process.argv[2] ? path.resolve(process.argv[2]) : path.join(OUT, "Dashboard.xlsx");
const FONT = "Arial";
const NAVY = "#12304A";
const BLUE = "#1F6E8C";
const PALE = "#EAF3F6";
const AMBER = "#FFF2CC";
const RED = "#FCE8E6";
const GREEN = "#E2F0D9";
const TEXT = "#18323F";
const MUTED = "#60727C";

function parseCsv(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (ch === '"') {
      if (quoted && text[i + 1] === '"') { field += '"'; i += 1; }
      else quoted = !quoted;
    } else if (ch === "," && !quoted) { row.push(field); field = ""; }
    else if ((ch === "\n" || ch === "\r") && !quoted) {
      if (ch === "\r" && text[i + 1] === "\n") i += 1;
      row.push(field); field = "";
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
    } else field += ch;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const [headers, ...body] = rows;
  return body.map((values) => Object.fromEntries(headers.map((key, i) => [key, values[i] ?? ""])));
}

function number(value) {
  return value === "" || value == null ? null : Number(value);
}

function styleHeader(range) {
  range.format = {
    fill: NAVY,
    font: { name: FONT, size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "inside", style: "thin", color: "#FFFFFF" },
  };
}

function writeTable(sheet, startRow, headers, rows, name) {
  const range = sheet.getRangeByIndexes(startRow - 1, 0, rows.length + 1, headers.length);
  range.values = [headers, ...rows];
  styleHeader(range.getRow(0));
  const table = sheet.tables.add(range, true, name);
  table.style = "TableStyleMedium2";
  return range;
}

async function main() {
  const parserCheck = parseCsv('a,b\n"x,y",2\n');
  if (parserCheck[0].a !== "x,y" || parserCheck[0].b !== "2") throw new Error("CSV parser self-check failed");

  const [priorityText, masterText, metricsText, metricsJsonText] = await Promise.all([
    fs.readFile(path.join(DATA, "reef_priority_predictions.csv"), "utf8"),
    fs.readFile(path.join(DATA, "master_reef_tourism_dataset.csv"), "utf8"),
    fs.readFile(path.join(DATA, "model_evaluation_metrics.csv"), "utf8"),
    fs.readFile(path.join(ROOT, "output", "model_evaluation_metrics.json"), "utf8"),
  ]);
  const priority = parseCsv(priorityText);
  const master = parseCsv(masterText);
  const metrics = parseCsv(metricsText);
  const metricsSummary = JSON.parse(metricsJsonText);
  if (!priority.length || !master.length || !metrics.length) throw new Error("Dashboard inputs are empty");

  await fs.mkdir(AUDIT, { recursive: true });
  const workbook = Workbook.create();
  const dashboard = workbook.worksheets.add("Dashboard");
  const prioritySheet = workbook.worksheets.add("Priority_Data");
  const historySheet = workbook.worksheets.add("History_Data");
  const modelSheet = workbook.worksheets.add("Model_Check");
  for (const sheet of [dashboard, prioritySheet, historySheet, modelSheet]) {
    sheet.showGridLines = false;
  }
  dashboard.tabColor = NAVY;
  prioritySheet.tabColor = BLUE;

  const priorityRows = priority.map((r) => [
    r.island, number(r.priority_rank), r.state, number(r.live_coral_cover_pct),
    number(r.lcc_change_rate), number(r.noaa_max_dhw), number(r.predicted_next_change_pct_per_year),
    number(r.prediction_lower), number(r.prediction_upper), r.priority_tier, r.evidence,
    r.recommended_next_step, r.confidence,
  ]);
  writeTable(prioritySheet, 1,
    ["Island", "Rank", "State", "Current LCC (%)", "Observed change (pp/yr)", "Max DHW (context only)", "Predicted next change (pp/yr)", "Lower", "Upper", "Priority tier", "Evidence", "Recommended next step", "Source confidence"],
    priorityRows, "PriorityTable");
  prioritySheet.freezePanes.freezeRows(1);
  prioritySheet.getRange("A:M").format.verticalAlignment = "center";
  prioritySheet.getRange("D2:I41").format.numberFormat = "0.0";
  prioritySheet.getRange("A:A").format.columnWidth = 18;
  prioritySheet.getRange("B:B").format.columnWidth = 8;
  prioritySheet.getRange("C:C").format.columnWidth = 14;
  prioritySheet.getRange("D:J").format.columnWidth = 19;
  prioritySheet.getRange("K:M").format.columnWidth = 42;
  prioritySheet.getRange("K2:M41").format.wrapText = true;
  prioritySheet.getRange("J2:J41").conditionalFormats.add("containsText", { text: "High", format: { fill: RED, font: { bold: true, color: "#9C0006" } } });

  const historyRows = master.map((r) => [
    r.island, r.state, number(r.survey_year), number(r.live_coral_cover_pct),
    number(r.lcc_change_rate), number(r.noaa_max_dhw), r.confidence,
  ]);
  writeTable(historySheet, 1,
    ["Island", "State", "Survey year", "Live coral cover (%)", "Observed change (pp/yr)", "Max DHW (context only)", "Source confidence"],
    historyRows, "HistoryTable");
  historySheet.freezePanes.freezeRows(1);
  historySheet.getRange("A:A").format.columnWidth = 18;
  historySheet.getRange("B:B").format.columnWidth = 14;
  historySheet.getRange("C:F").format.columnWidth = 20;
  historySheet.getRange("G:G").format.columnWidth = 42;
  historySheet.getRange("D2:F405").format.numberFormat = "0.0";

  const metricRows = metrics.map((r) => [r.Model, number(r["MAE (%/yr)"]), number(r["RMSE (%/yr)"]), number(r["R2 Score"])]);
  writeTable(modelSheet, 1, ["Model", "MAE (pp/yr)", "RMSE (pp/yr)", "R²"], metricRows, "ModelTable");
  modelSheet.getRange("A:A").format.columnWidth = 24;
  modelSheet.getRange("B:D").format.columnWidth = 18;
  modelSheet.getRange("B2:D5").format.numberFormat = "0.000";
  modelSheet.getRange("F1:G5").values = [
    ["Check", "Value"],
    ["Evaluation design", metricsSummary.validation],
    ["Forward evaluation rows", metricsSummary.evaluation_observations],
    ["Best-model MAE improvement", metricsSummary.mae_improvement_pct / 100],
    ["Decision status", "Screening only. NOAA heat is context, not a production-model feature."],
  ];
  styleHeader(modelSheet.getRange("F1:G1"));
  modelSheet.getRange("F:F").format.columnWidth = 26;
  modelSheet.getRange("G:G").format.columnWidth = 45;
  modelSheet.getRange("G4").format.numberFormat = "0.0%";
  const trend = new Map();
  for (const row of master) {
    const year = number(row.survey_year), lcc = number(row.live_coral_cover_pct);
    if (year == null || lcc == null) continue;
    const bucket = trend.get(year) ?? [];
    bucket.push(lcc);
    trend.set(year, bucket);
  }
  const trendRows = [...trend.entries()].sort(([a], [b]) => a - b).map(([year, values]) => [year, values.reduce((a, b) => a + b, 0) / values.length]);
  modelSheet.getRangeByIndexes(6, 5, trendRows.length + 1, 2).values = [["Survey year", "National mean LCC (%)"], ...trendRows];
  styleHeader(modelSheet.getRange("F7:G7"));
  modelSheet.getRange(`G8:G${trendRows.length + 7}`).format.numberFormat = "0.0";

  dashboard.getRange("A2:M2").format.borders = { bottom: { style: "medium", color: BLUE } };
  dashboard.getRange("A2").values = [["ReefSafe decision dashboard"]];
  dashboard.getRange("A2").format.font = { name: FONT, size: 16, bold: true, color: NAVY };
  dashboard.getRange("A3").values = [["Observed reef evidence + cautious next-observation screening | Malaysia, 2012–2025"]];
  dashboard.getRange("A3").format.font = { name: FONT, size: 10, italic: true, color: MUTED };

  dashboard.getRange("A5").values = [["Selected island"]];
  dashboard.getRange("A5").format.font = { name: FONT, size: 10, bold: true, color: TEXT };
  dashboard.getRange("B5:D5").format = { fill: AMBER, font: { name: FONT, size: 11, bold: true, color: NAVY }, borders: { preset: "outside", style: "dashed", color: BLUE }, horizontalAlignment: "center", verticalAlignment: "center" };
  dashboard.getRange("B5").values = [[priorityRows[0][0]]];
  dashboard.getRange("B5").dataValidation = { rule: { type: "list", formula1: `Priority_Data!$A$2:$A$${priorityRows.length + 1}` } };
  dashboard.getRange("E5:M5").values = [["Change the yellow cell to inspect any monitored island", null, null, null, null, null, null, null, null]];
  dashboard.getRange("E5:M5").format.font = { name: FONT, size: 9, italic: true, color: MUTED };

  const lastPriorityRow = priorityRows.length + 1;
  const lookup = (column) => `=IFERROR(VLOOKUP($B$5,Priority_Data!$A$2:$M$${lastPriorityRow},${column},FALSE),"")`;
  const cardLabels = [["Current LCC", null, null, "Observed change", null, null, "Predicted next change", null, null, "Priority", null, null, null]];
  dashboard.getRange("A7:M7").values = cardLabels;
  for (const address of ["A7:C7", "D7:F7", "G7:I7", "J7:M7"]) dashboard.getRange(address).format = { fill: PALE, font: { name: FONT, size: 9, bold: true, color: MUTED } };
  dashboard.getRange("A8").formulas = [[lookup(4)]];
  dashboard.getRange("D8").formulas = [[lookup(5)]];
  dashboard.getRange("G8").formulas = [[lookup(7)]];
  dashboard.getRange("J8").formulas = [[lookup(10)]];
  dashboard.getRange("A8:I8").format.font = { name: FONT, size: 14, bold: true, color: NAVY };
  dashboard.getRange("J8:M8").format.font = { name: FONT, size: 11, bold: true, color: "#9C0006" };
  dashboard.getRange("A8").format.numberFormat = '0.0"%"';
  dashboard.getRange("D8:G8").format.numberFormat = '0.0" pp/yr"';

  dashboard.getRange("A10").values = [["Uncertainty interval"]];
  dashboard.getRange("A10").format.font = { name: FONT, size: 9, bold: true, color: MUTED };
  dashboard.getRange("B10").formulas = [[`=IFERROR(TEXT(VLOOKUP($B$5,Priority_Data!$A$2:$M$${lastPriorityRow},8,FALSE),"0.0")&" to "&TEXT(VLOOKUP($B$5,Priority_Data!$A$2:$M$${lastPriorityRow},9,FALSE),"0.0")&" pp/yr","")`]];
  dashboard.getRange("B10:D10").format.font = { name: FONT, size: 10, bold: true, color: TEXT };
  dashboard.getRange("E10:M10").values = [["Intervals are empirical screening bands, not causal or site-specific certainty.", null, null, null, null, null, null, null, null]];
  dashboard.getRange("E10:M10").format.font = { name: FONT, size: 9, italic: true, color: MUTED };

  dashboard.getRange("A12:M12").values = [["Observed evidence", null, null, null, null, null, null, null, null, null, null, null, null]];
  dashboard.getRange("A12:M12").format = { fill: NAVY, font: { name: FONT, size: 10, bold: true, color: "#FFFFFF" } };
  dashboard.getRange("A13").formulas = [[lookup(11)]];
  dashboard.mergeCells("A13:M13");
  dashboard.getRange("A13:M13").format = { fill: "#FFFFFF", font: { name: FONT, size: 10, color: TEXT }, wrapText: true, verticalAlignment: "top" };
  dashboard.getRange("A15:M15").values = [["Recommended next step", null, null, null, null, null, null, null, null, null, null, null, null]];
  dashboard.getRange("A15:M15").format = { fill: BLUE, font: { name: FONT, size: 10, bold: true, color: "#FFFFFF" } };
  dashboard.getRange("A16").formulas = [[lookup(12)]];
  dashboard.mergeCells("A16:M16");
  dashboard.getRange("A16:M16").format = { fill: GREEN, font: { name: FONT, size: 10, bold: true, color: TEXT }, wrapText: true, verticalAlignment: "top" };

  const topHeaders = ["Island", "State", "Current LCC", "Predicted change", "Evidence"];
  dashboard.getRange("A37:E37").values = [topHeaders];
  styleHeader(dashboard.getRange("A37:E37"));
  for (let i = 0; i < 10; i += 1) {
    const row = 38 + i, source = 2 + i;
    dashboard.getRange(`A${row}:E${row}`).formulas = [[
      `=Priority_Data!A${source}`, `=Priority_Data!C${source}`, `=Priority_Data!D${source}`,
      `=Priority_Data!G${source}`, `=Priority_Data!K${source}`,
    ]];
  }
  dashboard.getRange("C38:D47").format.numberFormat = "0.0";
  dashboard.getRange("A38:E47").format.borders = { bottom: { style: "thin", color: "#D9E2E7" } };
  dashboard.getRange("E38:E47").format.wrapText = true;

  dashboard.getRange("H37:K37").values = [["Model", "MAE", "RMSE", "R²"]];
  styleHeader(dashboard.getRange("H37:K37"));
  for (let i = 0; i < metricRows.length; i += 1) {
    const row = 38 + i, source = 2 + i;
    dashboard.getRange(`H${row}:K${row}`).formulas = [[`=Model_Check!A${source}`, `=Model_Check!B${source}`, `=Model_Check!C${source}`, `=Model_Check!D${source}`]];
  }
  dashboard.getRange("I38:K41").format.numberFormat = "0.000";
  dashboard.getRange("H43").values = [["Model check"]];
  dashboard.mergeCells("H43:H44");
  const best = metricsSummary.model_comparison[metricsSummary.best_candidate];
  dashboard.getRange("I43").values = [[`${metricsSummary.best_candidate} MAE ${best.MAE.toFixed(2)} pp/yr vs baseline ${metricsSummary.baseline_mae.toFixed(2)} pp/yr (+${metricsSummary.mae_improvement_pct.toFixed(1)}%). R² ${best.R2.toFixed(3)}. NOAA heat is context only. Use the model to rank field checks, not as proof of tourism causality.`]];
  dashboard.mergeCells("I43:M44");
  dashboard.getRange("H43:M44").format = { fill: RED, font: { name: FONT, size: 9, bold: true, color: "#9C0006" }, wrapText: true, verticalAlignment: "top" };

  const rankChart = dashboard.charts.add("bar", [prioritySheet.getRange("A1:A11"), prioritySheet.getRange("G1:G11")]);
  rankChart.title = "Top 10 screening priorities: predicted next change (pp/yr)";
  rankChart.titleTextStyle.typeface = FONT;
  rankChart.titleTextStyle.fontSize = 12;
  rankChart.hasLegend = false;
  rankChart.xAxis = { axisType: "textAxis", textStyle: { typeface: FONT, fontSize: 9 } };
  rankChart.yAxis = { numberFormatCode: "0.0", numberFormatSourceLinked: false, textStyle: { typeface: FONT, fontSize: 9 } };
  rankChart.setPosition("A19", "F34");
  rankChart.series.items[0].fill = BLUE;

  const modelChart = dashboard.charts.add("line", modelSheet.getRange(`F7:G${trendRows.length + 7}`));
  modelChart.title = "Observed national mean live coral cover (%)";
  modelChart.titleTextStyle.typeface = FONT;
  modelChart.titleTextStyle.fontSize = 12;
  modelChart.hasLegend = false;
  modelChart.xAxis = { axisType: "textAxis", textStyle: { typeface: FONT, fontSize: 9 } };
  modelChart.yAxis = { numberFormatCode: "0.0", numberFormatSourceLinked: false, textStyle: { typeface: FONT, fontSize: 9 } };
  modelChart.setPosition("H19", "M34");
  modelChart.series.items[0].line = { fill: "#78909C", style: "solid", width: 2 };

  dashboard.getRange("A:M").format.font = { name: FONT, size: 10, color: TEXT };
  dashboard.getRange("A:A").format.columnWidth = 17;
  dashboard.getRange("B:D").format.columnWidth = 14;
  dashboard.getRange("E:E").format.columnWidth = 34;
  dashboard.getRange("F:M").format.columnWidth = 14;
  dashboard.getRange("13:13").format.rowHeight = 38;
  dashboard.getRange("16:16").format.rowHeight = 42;
  dashboard.getRange("38:47").format.rowHeight = 30;

  workbook.recalculate();
  const summary = await workbook.inspect({ kind: "workbook,sheet,table,drawing", maxChars: 6000, tableMaxRows: 3, tableMaxCols: 6 });
  const formulas = await workbook.inspect({ kind: "formula", sheetId: "Dashboard", range: "A1:M50", maxChars: 8000, options: { maxResults: 80 } });
  const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "formula error scan" });
  await fs.writeFile(path.join(AUDIT, "workbook_summary.txt"), summary.ndjson ?? String(summary));
  await fs.writeFile(path.join(AUDIT, "formula_check.txt"), formulas.ndjson ?? String(formulas));
  await fs.writeFile(path.join(AUDIT, "formula_errors.txt"), errors.ndjson ?? String(errors));

  for (const sheetName of ["Dashboard", "Priority_Data", "History_Data", "Model_Check"]) {
    const preview = await workbook.render({ sheetName, autoCrop: "all", scale: sheetName === "Dashboard" ? 0.9 : 0.55, format: "png" });
    await fs.writeFile(path.join(AUDIT, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
  }
  const xlsx = await SpreadsheetFile.exportXlsx(workbook);
  await fs.mkdir(path.dirname(XLSX_PATH), { recursive: true });
  await xlsx.save(XLSX_PATH);
  console.log(`Built ${XLSX_PATH}`);
}

await main();
