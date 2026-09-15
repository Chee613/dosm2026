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
  document.getElementById("kpi-bleach").textContent = `${fmt(kpi.bleachingMortality)}%`;
  document.getElementById("kpi-bleach-note").textContent =
    `${fmt(kpi.bleachingCoralsBleached)}% of corals bleached; Terengganu archipelago ${fmt(kpi.bleachingTerengganuMortality)}% mortality`;

  // Reef Check Malaysia condition bands (after Gomez et al. 1981), measured on live coral
  // cover including soft coral; a reef within 3 pp of a boundary could sit in either band.
  function reefCheckBand(cover) {
    const label = cover < 25 ? "Poor" : cover < 50 ? "Fair" : cover < 75 ? "Good" : "Excellent";
    const distance = Math.min(...[25, 50, 75].map((edge) => Math.abs(cover - edge)));
    return { label, borderline: distance < 3, distance };
  }

  function renderMap() {
    if (!window.L) return;
    // Wheel zoom off, so scrolling the page past the map does not zoom it instead.
    const map = L.map("map", { scrollWheelZoom: false }).setView([4.3, 108.5], 5);
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
    document.getElementById("top-priority-table").innerHTML = data.priorityIslands.slice(0, 10).map((unit) => {
      const band = reefCheckBand(unit.lcc);
      const bandTip = band.borderline
        ? `Reef Check band: ${band.label}, within ${fmt(band.distance)} pp of a boundary`
        : `Reef Check band: ${band.label}`;
      const isHigh = unit.tier === "High screening priority";
      return `
      <tr data-island="${escapeHtml(unit.island)}">
        <td>${unit.rank}</td><td><button class="table-link" type="button">${escapeHtml(unit.island)}</button></td>
        <td>${escapeHtml(unit.state)}</td>
        <td title="${escapeHtml(bandTip)}">${fmt(unit.lcc)}%${band.borderline ? " ≈" : ""}</td>
        <td>${fmt(unit.predictedNextChange, 2)} pp/year<br><small>${fmt(unit.predictionLower, 1)} to ${fmt(unit.predictionUpper, 1)}</small></td>
        <td><span class="kpi-pill ${isHigh ? "pill-red" : "pill-amber"}">${isHigh ? "High Priority" : "Monitor"}</span></td>
      </tr>`;
    }).join("");
    document.querySelectorAll("#top-priority-table tr").forEach((row) => row.addEventListener("click", () => selectUnit(row.dataset.island)));

    // The queue is ranked by predicted change, so the most degraded reefs can sit far
    // down it. Name them rather than let the table imply every struggling reef is listed.
    const lowest = [...data.priorityIslands].sort((a, b) => a.lcc - b.lcc).slice(0, 3);
    document.getElementById("queue-note").textContent =
      "Ranked by predicted change, not by condition: the lowest-cover units (" +
      lowest.map((unit) => `${unit.island} ${fmt(unit.lcc)}%`).join(", ") +
      `) sit at ranks ${lowest.map((unit) => unit.rank).join(", ")}. Hover a cover value for its Reef Check band; ≈ marks a unit within 3 pp of a band boundary.`;
  }

  function renderReefEconomy() {
    const economics = data.tourismEconomics;
    const rows = data.islandEconomics || [];
    if (!economics || !rows.length) return;
    document.getElementById("economy-value").textContent = money(economics.measured_reef_adjacent_rm);
    document.getElementById("economy-coverage").textContent = `${economics.islands_measured} of ${economics.islands_total} units measured`;
    document.getElementById("economy-split").innerHTML =
      `${Math.round(economics.measured_visitors).toLocaleString("en-MY")} visitors/year<br>${money(economics.measured_spending_rm)} tourism spending`;
    document.getElementById("economy-body").innerHTML = rows.slice(0, 6).map((row) => `
      <tr data-island="${escapeHtml(row.island)}">
        <td><button class="table-link" type="button">${escapeHtml(row.island)}</button><br><small>rank ${row.priority_rank}</small></td>
        <td><small>${escapeHtml(row.basis)}</small></td>
        <td>${money(row.spending_rm)}</td>
        <td><strong>${money(row.reef_adjacent_rm)}</strong></td>
      </tr>`).join("");
    document.querySelectorAll("#economy-body tr").forEach((row) => row.addEventListener("click", () => selectUnit(row.dataset.island)));
    document.getElementById("economy-source").textContent =
      `${economics.sources.reef_adjacent} ${economics.sources.spend} ${economics.sources.arrivals} ` +
      "An annual flow attributable to reef presence, not an asset value, and not a forecast of losses from coral decline.";
  }

  function renderSeasonRest() {
    const economics = data.tourismEconomics;
    if (!economics) return;
    const rest = economics.tradeoff;
    const [low, high] = rest.recovery_years;
    document.getElementById("rest-scenario").textContent =
      `One month of rest on the ${rest.islands_measured} of ${rest.islands_total} high-priority units with published arrivals (${rest.island_names.join(", ")})`;
    document.getElementById("rest-short").textContent = money(rest.short_term_loss_rm);
    document.getElementById("rest-long").textContent = `${money(rest.long_term_low_rm)} – ${money(rest.long_term_high_rm)}`;
    document.getElementById("rest-short-note").textContent = "Foregone tourism spending on these units for one month.";
    document.getElementById("rest-long-note").textContent =
      `Reef-adjacent value of ${money(rest.reef_adjacent_annual_rm)}/year held over a ${low}–${high} year recovery window.`;
    const widest = Math.max(rest.short_term_loss_rm, rest.long_term_high_rm) || 1;
    document.getElementById("rest-short-bar").style.width = `${Math.max(2, 100 * rest.short_term_loss_rm / widest)}%`;
    document.getElementById("rest-long-bar").style.width = `${100 * rest.long_term_high_rm / widest}%`;
    document.getElementById("rest-callout").textContent =
      `${economics.sources.recovery} A reef that is lost stops earning for that whole window, while a rest costs one month.`;
    document.getElementById("rest-source").textContent =
      `${rest.ratio_note} Arithmetic on published arrivals, not a prediction: it assumes rested-month visitors do not return later and does not model how coral responds to a rest.`;
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
        <line x1="${left}" y1="${y(50)}" x2="${width-right}" y2="${y(50)}" stroke="#94a3b8" stroke-dasharray="5 4"/>
        <line x1="${left}" y1="${y(25)}" x2="${width-right}" y2="${y(25)}" stroke="#dc2626" stroke-dasharray="5 4"/>
        <polyline points="${points}" fill="none" stroke="#0f766e" stroke-width="3"/>
        ${rows.map((row) => `<circle cx="${x(row.year)}" cy="${y(row.lcc)}" r="4" fill="#0284c7"><title>${row.year}: ${fmt(row.lcc)}%</title></circle>`).join("")}
        <text x="${left}" y="${height-10}" font-size="12">${minYear}</text><text x="${width-right}" y="${height-10}" text-anchor="end" font-size="12">${maxYear}</text>
        <text x="${left+4}" y="${y(50)-5}" font-size="11" fill="#475569">50% Fair/Good boundary (Reef Check)</text>
        <text x="${left+4}" y="${y(25)-5}" font-size="11" fill="#b91c1c">25% Poor/Fair boundary (Reef Check)</text>
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
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Verified 2000 to 2017 state marine-park visitor totals and the gap after 2017" style="width:100%;height:auto">
        <line x1="${left}" y1="${height-bottom}" x2="${width-10}" y2="${height-bottom}" stroke="#94a3b8"/>
        ${bars}
        <rect x="${left+plotWidth}" y="${top}" width="${gapWidth}" height="${height-top-bottom}" fill="#fee2e2"/>
        <text x="${left+plotWidth+gapWidth/2}" y="95" text-anchor="middle" font-size="13" fill="#991b1b">No state series</text>
        <text x="${left+plotWidth+gapWidth/2}" y="113" text-anchor="middle" font-size="13" fill="#991b1b">after 2017</text>
        <text x="${left+plotWidth+gapWidth/2}" y="145" text-anchor="middle" font-size="11" fill="#475569">2024: arrivals published</text>
        <text x="${left+plotWidth+gapWidth/2}" y="160" text-anchor="middle" font-size="11" fill="#475569">for 11 units only</text>
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
  renderReefEconomy();
  renderSeasonRest();
  renderTourismGap();
  renderValidation();
  const initial = data.priorityIslands[0];
  if (initial) selectUnit(initial.island, false);
}());
