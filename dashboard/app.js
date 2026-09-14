(function () {
  "use strict";

  const data = window.REEFSAFE_DATA;
  const ECONOMIC_VALUATION = window.ECONOMIC_VALUATION;
  const TOURISM_DATA_GAP = window.TOURISM_DATA_GAP;
  if (!data) return;

  const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[char]));
  const fmt = (value, digits = 1) => Number(value).toFixed(digits);
  const money = (value) => value >= 1e9 ? `RM${fmt(value / 1e9, 2)}B` : `RM${fmt(value / 1e6, 2)}M`;

  document.querySelectorAll(".nav-tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".nav-tab").forEach((item) => item.classList.toggle("active", item === button));
      document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === `tab-${button.dataset.tab}`));
      if (button.dataset.tab === "overview" && window.reefMap) setTimeout(() => window.reefMap.invalidateSize(), 0);
    });
  });

  const kpi = data.nationalKPIs;
  document.getElementById("kpi-cover").textContent = `${fmt(kpi.latestMeanCoralCover)}%`;
  document.getElementById("kpi-cover-note").textContent = `${kpi.surveyedUnits} units observed in ${kpi.latestSurveyYear}`;
  document.getElementById("kpi-paired").textContent = `${fmt(kpi.pairedChange2024To2025, 2)} pp`;
  document.getElementById("kpi-paired-note").textContent = `Same ${kpi.pairedUnits} units in both years`;
  document.getElementById("kpi-priority").textContent = `${kpi.priorityCount} / ${kpi.surveyedUnits}`;

  function renderMap() {
    if (!window.L) return;
    const map = L.map("map").setView([4.3, 108.5], 5);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);
    data.priorityIslands.forEach((unit) => {
      const color = unit.tier === "High screening priority" ? "#b91c1c" : "#0f766e";
      L.circleMarker([unit.lat, unit.lng], { radius: 7, color, fillColor: color, fillOpacity: 0.75 })
        .bindPopup(`<strong>${escapeHtml(unit.island)}</strong><br>Observed cover: ${fmt(unit.lcc)}%<br>Screening rank: ${unit.rank}`)
        .addTo(map)
        .on("click", () => selectUnit(unit.island));
    });
    window.reefMap = map;
  }

  function renderEconomics() {
    const max = Math.max(...ECONOMIC_VALUATION.components.map((item) => item.annual_value_myr));
    document.getElementById("economic-pillars-chart").innerHTML = ECONOMIC_VALUATION.components.map((item) => `
      <div style="margin:12px 0">
        <div style="display:flex;justify-content:space-between;gap:12px"><span>${escapeHtml(item.component)}</span><strong>${money(item.annual_value_myr)}</strong></div>
        <div style="height:10px;background:#e2e8f0;border-radius:5px"><div style="width:${Math.max(1, 100 * item.annual_value_myr / max)}%;height:100%;background:#0f766e;border-radius:5px"></div></div>
        <small>Source page ${item.source_page}</small>
      </div>`).join("");
    document.getElementById("economic-source-note").innerHTML = `${escapeHtml(ECONOMIC_VALUATION.scope_note)}. <a href="${ECONOMIC_VALUATION.source_url}" target="_blank" rel="noopener">Primary source</a>.`;
  }

  function renderQueue() {
    document.getElementById("top-priority-table").innerHTML = data.priorityIslands.slice(0, 10).map((unit) => `
      <tr data-island="${escapeHtml(unit.island)}">
        <td>${unit.rank}</td><td><button class="table-link" type="button">${escapeHtml(unit.island)}</button></td>
        <td>${escapeHtml(unit.state)}</td><td>${fmt(unit.lcc)}%</td>
        <td>${fmt(unit.predictedNextChange, 2)} pp/year<br><small>${fmt(unit.predictionLower, 1)} to ${fmt(unit.predictionUpper, 1)}</small></td>
        <td>${escapeHtml(unit.evidence)}</td>
      </tr>`).join("");
    document.querySelectorAll("#top-priority-table tr").forEach((row) => row.addEventListener("click", () => selectUnit(row.dataset.island)));
  }

  function renderHistory(name) {
    const rows = data.islandHistory[name] || [];
    if (!rows.length) return;
    const width = 620, height = 280, left = 48, top = 20, right = 20, bottom = 38;
    const years = rows.map((row) => row.year), values = rows.map((row) => row.lcc);
    const minYear = Math.min(...years), maxYear = Math.max(...years);
    const x = (year) => left + (year - minYear) / Math.max(1, maxYear - minYear) * (width - left - right);
    const y = (value) => top + (100 - value) / 100 * (height - top - bottom);
    const points = rows.map((row) => `${x(row.year)},${y(row.lcc)}`).join(" ");
    document.getElementById("island-history-chart").innerHTML = `
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Observed coral-cover history for ${escapeHtml(name)}" style="width:100%;height:auto">
        <line x1="${left}" y1="${y(40)}" x2="${width-right}" y2="${y(40)}" stroke="#f59e0b" stroke-dasharray="5 4"/>
        <polyline points="${points}" fill="none" stroke="#0f766e" stroke-width="3"/>
        ${rows.map((row) => `<circle cx="${x(row.year)}" cy="${y(row.lcc)}" r="4" fill="#0284c7"><title>${row.year}: ${fmt(row.lcc)}%</title></circle>`).join("")}
        <text x="${left}" y="${height-10}" font-size="12">${minYear}</text><text x="${width-right}" y="${height-10}" text-anchor="end" font-size="12">${maxYear}</text>
        <text x="${left+4}" y="${y(40)-5}" font-size="11" fill="#92400e">40% reference</text>
      </svg>`;
  }

  function selectUnit(name, navigate = true) {
    const unit = data.priorityIslands.find((item) => item.island === name);
    if (!unit) return;
    document.getElementById("island-select").value = name;
    document.getElementById("unit-title").textContent = `${unit.island} — screening rank ${unit.rank}`;
    document.getElementById("unit-summary").innerHTML = `
      <p><strong>Observed cover:</strong> ${fmt(unit.lcc)}% (${unit.surveyYear})</p>
      <p><strong>Next-observation estimate:</strong> ${fmt(unit.predictedNextChange, 2)} percentage points/year</p>
      <p><strong>Empirical forward-residual range:</strong> ${fmt(unit.predictionLower, 1)} to ${fmt(unit.predictionUpper, 1)}</p>
      <p><strong>Source confidence:</strong> ${escapeHtml(unit.sourceConfidence)}</p>`;
    document.getElementById("unit-evidence").innerHTML = `<strong>Verify:</strong> ${escapeHtml(unit.evidence)}<br><strong>Next step:</strong> ${escapeHtml(unit.nextStep)}`;
    renderHistory(name);
    if (navigate) document.querySelector('[data-tab="diagnostics"]').click();
  }

  function renderTourismGap() {
    const rows = TOURISM_DATA_GAP.annualTrend;
    const max = Math.max(...rows.map((row) => row.total));
    const width = 900, height = 250, left = 35, top = 15, bottom = 35, gapWidth = 170;
    const plotWidth = width - left - gapWidth - 20;
    const barWidth = plotWidth / rows.length - 6;
    const bars = rows.map((row, index) => {
      const x = left + index * (plotWidth / rows.length);
      const totalHeight = (height - top - bottom) * row.total / max;
      const domesticHeight = totalHeight * row.domestic / row.total;
      return `<rect x="${x}" y="${height-bottom-totalHeight}" width="${barWidth}" height="${domesticHeight}" fill="#0284c7"><title>${row.year}: ${row.domestic.toLocaleString()} domestic</title></rect>
        <rect x="${x}" y="${height-bottom-totalHeight+domesticHeight}" width="${barWidth}" height="${totalHeight-domesticHeight}" fill="#38bdf8"><title>${row.year}: ${row.foreign.toLocaleString()} foreign</title></rect>
        <text x="${x+barWidth/2}" y="${height-14}" text-anchor="middle" font-size="11">${row.year}</text>`;
    }).join("");
    document.getElementById("tourism-gap-chart").innerHTML = `
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Verified 2000 to 2009 visitor totals and island-level data gap" style="width:100%;height:auto">
        <line x1="${left}" y1="${height-bottom}" x2="${width-10}" y2="${height-bottom}" stroke="#94a3b8"/>
        ${bars}
        <rect x="${left+plotWidth}" y="${top}" width="${gapWidth}" height="${height-top-bottom}" fill="#fee2e2"/>
        <text x="${left+plotWidth+gapWidth/2}" y="105" text-anchor="middle" font-size="13" fill="#991b1b">No verified island-level</text>
        <text x="${left+plotWidth+gapWidth/2}" y="125" text-anchor="middle" font-size="13" fill="#991b1b">exposure series</text>
      </svg><p class="method-note">${escapeHtml(TOURISM_DATA_GAP.limitation)}</p>`;
  }

  function renderValidation() {
    document.getElementById("model-benchmark-table").innerHTML = data.validationByYear.map((row) => `
      <tr><td>${row.target_year}</td><td>${row.n}</td><td>${fmt(row.mae, 2)}</td><td>${fmt(row.r2, 2)}</td><td>${fmt(row.bias, 2)}</td></tr>`).join("");
    const metrics = data.modelMetrics;
    document.getElementById("model-note").textContent = `${metrics.best_candidate} improves MAE ${fmt(metrics.mae_improvement_pct, 1)}% over the mean baseline. Latest-year R² is weak, so outputs remain screening-only.`;
  }

  const select = document.getElementById("island-select");
  select.innerHTML = data.priorityIslands.map((unit) => `<option value="${escapeHtml(unit.island)}">${escapeHtml(unit.island)} — rank ${unit.rank}</option>`).join("");
  select.addEventListener("change", () => selectUnit(select.value));

  renderMap();
  renderEconomics();
  renderQueue();
  renderTourismGap();
  renderValidation();
  const initial = data.priorityIslands[0];
  if (initial) selectUnit(initial.island, false);
}());
