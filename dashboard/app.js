(function () {
  "use strict";

  const data = window.REEFSAFE_DATA;
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
      if (history.replaceState) history.replaceState(null, "", `#${button.dataset.tab}`);
      if (button.dataset.tab === "overview" && window.reefMap) setTimeout(() => window.reefMap.invalidateSize(), 0);
    });
  });

  const initHash = (location.hash || "").replace("#", "");
  if (initHash) {
    const targetTab = document.querySelector(`.nav-tab[data-tab="${initHash}"]`);
    if (targetTab) targetTab.click();
  }

  const kpi = data.nationalKPIs;
  document.getElementById("kpi-cover").textContent = `${fmt(kpi.latestMeanCoralCover)}%`;
  document.getElementById("kpi-cover-note").textContent = `${kpi.surveyedUnits} units surveyed`;
  document.getElementById("kpi-paired").textContent = `${fmt(kpi.pairedChange2024To2025, 2)} pp`;
  document.getElementById("kpi-paired-note").textContent = `Same ${kpi.pairedUnits} units in both years`;
  document.getElementById("kpi-priority").textContent = `${kpi.priorityCount} / ${kpi.surveyedUnits}`;
  document.getElementById("kpi-bleach").textContent = `${fmt(kpi.bleachingMortality)}%`;
  document.getElementById("kpi-bleach-note").textContent = `${fmt(kpi.bleachingCoralsBleached)}% of corals bleached`;

  const isHigh = (unit) => unit.tier === "High screening priority";
  const tierLabel = (unit) => (isHigh(unit) ? "High Priority" : "Monitor");
  const changeText = (value) => `${value > 0 ? "+" : ""}${fmt(value, 2)} pp/yr`;

  // Marker colour: screening tier first, then the sign of the predicted change.
  const MARKER_GROUPS = [
    { label: "High Priority", color: "#DC2626", test: (unit) => isHigh(unit) },
    { label: "Monitor, decline predicted", color: "#F59E0B", test: (unit) => !isHigh(unit) && unit.predictedNextChange < 0 },
    { label: "Monitor, gain predicted", color: "#10B981", test: (unit) => !isHigh(unit) && unit.predictedNextChange >= 0 },
  ];

  function renderMap() {
    if (!window.L) return;
    const map = L.map("map").setView([4.3, 108.5], 5);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);
    data.priorityIslands.forEach((unit) => {
      const group = MARKER_GROUPS.find((item) => item.test(unit));
      const popup = `
        <div class="map-popup">
          <strong>${escapeHtml(unit.island)}</strong>
          <span class="map-popup-state">${escapeHtml(unit.state)}</span>
          <div>Observed cover: <strong>${fmt(unit.lcc)}%</strong></div>
          <div>Predicted change: <strong style="color:${unit.predictedNextChange < 0 ? "#DC2626" : "#059669"}">${changeText(unit.predictedNextChange)}</strong></div>
          <div>Status tier: <strong>${tierLabel(unit)}</strong></div>
          <button type="button" class="map-popup-btn">View Diagnostics →</button>
        </div>`;
      L.circleMarker([unit.lat, unit.lng], {
        radius: isHigh(unit) ? 8 : 6, color: group.color, weight: 1.5, fillColor: group.color, fillOpacity: 0.85,
      })
        .bindPopup(popup)
        // Wire the button when the popup opens, so island names need no inline escaping.
        .on("popupopen", (event) => {
          event.popup.getElement().querySelector(".map-popup-btn")
            .addEventListener("click", () => selectUnit(unit.island), { once: true });
        })
        .addTo(map);
    });
    document.getElementById("map-legend").innerHTML = MARKER_GROUPS.map((group) => `
      <span class="map-key-item"><span class="map-key-dot" style="background:${group.color}"></span>${group.label} (${data.priorityIslands.filter(group.test).length})</span>`).join("");
    window.reefMap = map;
    // The printed page is narrower than the screen; refit the map before and after printing.
    window.addEventListener("beforeprint", () => map.invalidateSize());
    window.addEventListener("afterprint", () => map.invalidateSize());
    window.addEventListener("resize", () => map.invalidateSize());
  }

  function renderQueue() {
    document.getElementById("top-priority-table").innerHTML = data.priorityIslands.slice(0, 5).map((unit) => `
      <tr data-island="${escapeHtml(unit.island)}">
        <td>${unit.rank}</td>
        <td><button class="table-link" type="button">${escapeHtml(unit.island)}</button></td>
        <td>${escapeHtml(unit.state)}</td>
        <td>${fmt(unit.lcc)}%</td>
        <td title="Range: ${fmt(unit.predictionLower, 1)} to ${fmt(unit.predictionUpper, 1)} pp/yr">${changeText(unit.predictedNextChange)}</td>
        <td><span class="kpi-pill ${isHigh(unit) ? "pill-red" : "pill-amber"}">${tierLabel(unit)}</span></td>
      </tr>`).join("");
    document.querySelectorAll("#top-priority-table tr").forEach((row) => row.addEventListener("click", () => selectUnit(row.dataset.island)));

    // Ranked by predicted change, so the most degraded reefs can sit far down the list.
    const lowest = [...data.priorityIslands].sort((a, b) => a.lcc - b.lcc).slice(0, 3);
    document.getElementById("queue-note").textContent =
      `Ranked by predicted change, not condition. Lowest cover: ${lowest.map((unit) => `${unit.island} ${fmt(unit.lcc)}% (#${unit.rank})`).join(", ")}. Hover a prediction for its range.`;
  }

  // DMPM Total Economic Value as a donut. Components under 1.5% get a 1.5% slice so all
  // seven stay visible; the larger ones share the rest in proportion. The legend and
  // hover text keep the true shares.
  const POTENTIAL_COLOURS = ["#0F766E", "#0284C7", "#6366F1", "#64748B", "#A855F7", "#F59E0B", "#84CC16"];
  const MIN_SLICE = 1.5;

  function renderReefPotential() {
    const tev = data.economicValuation;
    if (!tev) return;
    const parts = [...tev.components].sort((a, b) => b.annual_value_myr - a.annual_value_myr);
    const sum = parts.reduce((total, part) => total + part.annual_value_myr, 0);
    const trueShare = parts.map((part) => 100 * part.annual_value_myr / sum);
    const small = trueShare.map((share) => share < MIN_SLICE);
    const reserved = MIN_SLICE * small.filter(Boolean).length;
    const largeTotal = trueShare.reduce((total, share, index) => total + (small[index] ? 0 : share), 0);
    const shown = trueShare.map((share, index) => (small[index] ? MIN_SLICE : share * (100 - reserved) / largeTotal));
    const pct = (share) => `${fmt(share, share >= 1 ? 1 : 2)}%`;

    const cx = 80, cy = 80, r = 58, gap = 0.3;
    let offset = 0;
    const slices = parts.map((part, index) => {
      const length = shown[index] - gap;
      const slice = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${POTENTIAL_COLOURS[index]}" stroke-width="24" pathLength="100"
          stroke-dasharray="${length} ${100 - length}" stroke-dashoffset="${-offset}">
          <title>${escapeHtml(part.component)}: ${money(part.annual_value_myr)} a year, ${pct(trueShare[index])} (DMPM p.${part.source_page})</title></circle>`;
      offset += shown[index];
      return slice;
    }).join("");
    const legend = parts.map((part, index) => `
      <span class="map-key-dot" style="background:${POTENTIAL_COLOURS[index]}"></span>
      <span>${escapeHtml(part.component)}</span>
      <span class="potential-value">${money(part.annual_value_myr)}</span>
      <span class="potential-pct">${pct(trueShare[index])}</span>`).join("");

    document.getElementById("reef-potential-donut").innerHTML = `
      <svg viewBox="0 0 160 160" role="img" aria-label="${escapeHtml(parts.map((part, index) => `${part.component} ${pct(trueShare[index])}`).join("; "))}">
        <g transform="rotate(-90 ${cx} ${cy})">${slices}</g>
        <text x="${cx}" y="${cy + 2}" text-anchor="middle" font-size="17" font-weight="700" fill="#0F172A">RM${fmt(tev.reported_total_myr / 1e9, 1)}B</text>
        <text x="${cx}" y="${cy + 18}" text-anchor="middle" font-size="10" fill="#64748B">per year</text>
      </svg>
      <div class="potential-legend">${legend}</div>`;
  }

  function renderReefEconomy() {
    const economics = data.tourismEconomics;
    const rows = data.parkEconomics || [];
    if (!economics || !rows.length) return;
    document.getElementById("economy-value").textContent = money(economics.national_reef_adjacent_rm);
    document.getElementById("economy-coverage").textContent = `${economics.units_covered} of ${economics.units_total} units`;
    document.getElementById("economy-split").innerHTML =
      `${Math.round(economics.national_visitors).toLocaleString("en-MY")} visitors/yr<br>${money(economics.national_spending_rm)} spending`;
    document.getElementById("economy-body").innerHTML = rows.map((row) => `
      <tr>
        <td title="Units: ${escapeHtml(row.units)}"><strong>${escapeHtml(row.park)}</strong> <small class="park-state">${escapeHtml(row.state)}</small></td>
        <td title="${escapeHtml(row.basis)}">${row.visitors_per_year.toLocaleString("en-MY")}</td>
        <td>${money(row.spending_rm)}</td>
        <td><strong>${money(row.reef_adjacent_rm)}</strong></td>
      </tr>`).join("");
    document.getElementById("economy-caption").textContent =
      `${rows.length} parks. Excludes Malacca and non-park reefs (${economics.units_excluded.length} units).`;
  }

  function renderSeasonRest() {
    const economics = data.tourismEconomics;
    if (!economics) return;
    const rest = economics.tradeoff;
    const [lowYears, highYears] = rest.recovery_years;
    document.getElementById("rest-scenario").textContent =
      `One month of rest across ${rest.park_names.length} parks holding ${rest.units_covered} of ${rest.units_total} high-priority units`;
    document.getElementById("rest-scenario").title =
      `Parks: ${rest.park_names.join(", ")}. Not covered: ${rest.units_uncovered_names.join(", ") || "none"}.`;
    document.getElementById("rest-short").textContent = `-${money(rest.short_term_loss_rm)}`;
    document.getElementById("rest-long-low").textContent = `+${money(rest.long_term_low_rm)}`;
    document.getElementById("rest-long-high").textContent = `+${money(rest.long_term_high_rm)}`;
    renderRestBars([
      { label: "One month of rest", value: rest.short_term_loss_rm, kind: "rest" },
      { label: `Reef revenue, ${lowYears} yrs`, value: rest.long_term_low_rm, kind: "revenue" },
      { label: `Reef revenue, ${highYears} yrs`, value: rest.long_term_high_rm, kind: "revenue" },
    ]);
  }

  // Horizontal bars on one RM-millions axis, gridlines every 50M.
  function renderRestBars(rows) {
    const step = 50;
    const max = Math.ceil(Math.max(...rows.map((row) => row.value)) / 1e6 / step) * step;
    const ticks = Array.from({ length: max / step + 1 }, (_, index) => index * step);
    const labelEvery = window.innerWidth < 640 ? 2 : 1;
    // Rest is a loss, reef revenue a gain.
    const signed = (row) => `${row.kind === "rest" ? "-" : "+"}${money(row.value)}`;
    const chart = document.getElementById("rest-bars");
    chart.setAttribute("aria-label", rows.map((row) => `${row.label} ${signed(row)}`).join("; "));
    chart.innerHTML = `
      <div class="hbar-labels">${rows.map((row) => `<span>${escapeHtml(row.label)}</span>`).join("")}</div>
      <div class="hbar-plot">
        ${ticks.map((tick) => `<span class="hbar-grid" style="left:${100 * tick / max}%"></span>`).join("")}
        ${rows.map((row) => `<div class="hbar-row"><div class="hbar hbar-${row.kind}" style="width:${100 * row.value / 1e6 / max}%" title="${escapeHtml(row.label)}: ${signed(row)}"></div></div>`).join("")}
        <div class="hbar-ticks">${ticks.map((tick, index) => index % labelEvery ? "" : `<span style="left:${100 * tick / max}%">${tick}</span>`).join("")}</div>
      </div>
      <div class="hbar-axis-title">RM millions</div>`;
  }

  // Observed surveys (solid) plus the model's next-year point (dashed; red for a
  // predicted decline, green for a gain): latest cover + predicted change x 1 year.
  function renderHistory(unit) {
    const rows = data.islandHistory[unit.island] || [];
    if (!rows.length) return;
    const last = rows[rows.length - 1];
    const next = { year: last.year + 1, lcc: Math.min(100, Math.max(0, last.lcc + unit.predictedNextChange)) };
    const colour = unit.predictedNextChange < 0 ? "#DC2626" : "#059669";
    // Narrow screens get a narrower drawing so the SVG text stays readable.
    const narrow = window.innerWidth < 640;
    const width = narrow ? 420 : 1000, height = narrow ? 240 : 175, left = 44, top = 14, right = narrow ? 96 : 140, bottom = 28;
    const x = (year) => left + (year - rows[0].year) / Math.max(1, next.year - rows[0].year) * (width - left - right);
    const y = (value) => top + (100 - value) / 100 * (height - top - bottom);
    const grid = [0, 25, 50, 75, 100].map((value) => `
      <line x1="${left}" y1="${y(value)}" x2="${width-right}" y2="${y(value)}" stroke="#E2E8F0"/>
      <text x="${left-6}" y="${y(value)+4}" text-anchor="end" font-size="11" fill="#64748B">${value}%</text>`).join("");
    const bands = [[50, "Fair/Good", "#94A3B8", "#475569"], [25, "Poor/Fair", "#DC2626", "#B91C1C"]].map(([value, label, line, text]) => `
      <line x1="${left}" y1="${y(value)}" x2="${width-right}" y2="${y(value)}" stroke="${line}" stroke-dasharray="5 4"/>
      <text x="${width-right+(narrow ? 14 : 26)}" y="${y(value)+4}" font-size="11" fill="${text}">${value}% ${label}</text>`).join("");
    // Year labels from the predicted year backwards, skipping any that would overlap.
    const tickYears = [];
    for (const year of [next.year, ...rows.map((row) => row.year).reverse()]) {
      if (!tickYears.length || x(tickYears[tickYears.length - 1]) - x(year) >= 32) tickYears.push(year);
    }
    const ticks = tickYears.map((year) =>
      `<text x="${x(year)}" y="${height-12}" text-anchor="middle" font-size="11" fill="${year === next.year ? colour : "#64748B"}">${year}</text>`).join("");
    // Label below a falling point and above a rising one, so it never sits on the dashed line.
    const below = unit.predictedNextChange < 0 && y(next.lcc) + 20 < height - bottom;
    const changeSign = unit.predictedNextChange > 0 ? "+" : "";
    const changeDigits = Math.abs(unit.predictedNextChange) < 1 ? 2 : 1;
    const changeFormatted = `${changeSign}${fmt(unit.predictedNextChange, changeDigits)}%`;
    const changeTooltip = `${next.year} forecast: ${unit.predictedNextChange > 0 ? "increase of +" : "decrease of "}${fmt(Math.abs(unit.predictedNextChange), 2)}% (predicted cover: ${fmt(next.lcc)}%)`;
    document.getElementById("legend-predicted").style.borderTopColor = colour;
    document.getElementById("island-history-chart").innerHTML = `
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Observed and predicted coral cover for ${escapeHtml(unit.island)}" style="width:100%;height:auto">
        ${grid}${bands}
        <polyline points="${rows.map((row) => `${x(row.year)},${y(row.lcc)}`).join(" ")}" fill="none" stroke="#0F766E" stroke-width="3"/>
        <line x1="${x(last.year)}" y1="${y(last.lcc)}" x2="${x(next.year)}" y2="${y(next.lcc)}" stroke="${colour}" stroke-width="3" stroke-dasharray="7 5"/>
        ${rows.map((row) => `<circle cx="${x(row.year)}" cy="${y(row.lcc)}" r="4" fill="#0284C7"><title>${row.year}: ${fmt(row.lcc)}%</title></circle>`).join("")}
        <circle cx="${x(next.year)}" cy="${y(next.lcc)}" r="5.5" fill="#FFFFFF" stroke="${colour}" stroke-width="2.5"><title>${changeTooltip}</title></circle>
        <text x="${x(next.year)}" y="${below ? y(next.lcc) + 20 : y(next.lcc) - 11}" text-anchor="middle" font-size="12" font-weight="700" fill="${colour}"><title>${changeTooltip}</title>${changeFormatted}</text>
        ${ticks}
      </svg>`;
  }

  // Urgency uses the same three groups, in the same order, as the map colours.
  const URGENCY = ["High", "Medium", "Low"];

  // Diverging bars: decline extends left of the centre line, recovery to the right,
  // each scaled to the unit's largest group so the biggest push fills half the track.
  function renderStressBreakdown(stress, prediction) {
    const widest = Math.max(...stress.groups.map((group) => Math.abs(group.pp)), 0.01);
    const rows = stress.groups.map((group) => {
      const side = group.pp < 0 ? "decline" : "recovery";
      return `
        <div class="stress-row${group.stressor ? "" : " stress-context"}">
          <span class="stress-name">${escapeHtml(group.name)}${group.stressor ? "" : " <small>(context)</small>"}</span>
          <span class="stress-track"><span class="stress-bar stress-${side}" style="width:${50 * Math.abs(group.pp) / widest}%"></span></span>
          <span class="stress-value">${group.pp > 0 ? "+" : ""}${fmt(group.pp, 2)}</span>
        </div>`;
    }).join("");
    document.getElementById("stress-breakdown").innerHTML = `${rows}
      <div class="stress-total">Model baseline ${changeText(stress.baseline)} + factors = prediction ${changeText(prediction)}</div>`;
  }

  // Evidence for the top (or strongest) stressor: each input's surveyed value, how it
  // compares across the ranked units, and its own push on the prediction.
  const ordinal = (n) => `${n}${[, "st", "nd", "rd"][(n % 100 >> 3 ^ 1 && n % 10) || 0] || "th"}`;

  function evidenceValue(entry, surveyYear) {
    if (entry.value === null) return "Not recorded; the model used the median";
    if (entry.kind === "flag") {
      const said = entry.value >= 1 ? `Mentioned in the ${surveyYear} report` : "Not mentioned";
      return `${said} · mentioned for ${entry.mentioned} of ${entry.of} units`;
    }
    const show = (value) => entry.kind === "pct" ? `${fmt(value, 1)}%` : fmt(value, 2);
    const unit = { pct: " of substrate", count: " per 100 m²", ratio: "" }[entry.kind];
    // Count from whichever end is nearer: "3rd highest" or "2nd lowest".
    const joint = entry.ties > 1 ? "joint " : "";
    const fromBottom = entry.of - (entry.rank + entry.ties - 1) + 1;
    const place = entry.rank === 1 ? `${joint}highest`
      : fromBottom === 1 ? `${joint}lowest`
      : entry.rank <= fromBottom ? `${joint}${ordinal(entry.rank)} highest`
      : `${joint}${ordinal(fromBottom)} lowest`;
    return `${show(entry.value)}${unit} · ${place} of ${entry.of} (median ${show(entry.median)})`;
  }

  function renderUnitEvidence(stress, surveyYear) {
    const box = document.getElementById("unit-evidence");
    const reason = `
      <div class="evidence-head">Why this check · ${escapeHtml(stress.reportReason.label)}</div>
      <p class="evidence-note">${escapeHtml(stress.reportReason.detail)}</p>`;
    const evidence = stress.evidence;
    if (!evidence) {
      box.innerHTML = `${reason}<p class="evidence-empty">No measured stressor pushes this prediction towards decline.</p>`;
      return;
    }
    const threshold = evidence.belowThreshold
      ? ` · <span class="evidence-flag">strongest stressor, below the 0.25 pp/yr threshold</span>` : "";
    box.innerHTML = `${reason}
      <div class="evidence-head">Model's strongest stressor · ${escapeHtml(evidence.group)} · Reef Check Malaysia, ${surveyYear} survey${threshold}</div>
      ${evidence.items.length ? "" : `<p class="evidence-empty">No single input moved the prediction by 0.01 pp/yr or more.</p>`}
      <ul class="evidence-list">${evidence.items.map((entry) => `
        <li>
          <span class="evidence-name">${escapeHtml(entry.label)}</span>
          <span class="evidence-pp ${entry.pp < -0.005 ? "decline" : entry.pp > 0.005 ? "recovery" : ""}">${entry.pp > 0 ? "+" : ""}${fmt(entry.pp, 2)} pp/yr</span>
          <span class="evidence-detail">${escapeHtml(evidenceValue(entry, surveyYear))}</span>
        </li>`).join("")}
      </ul>
      <p class="evidence-note">${escapeHtml(evidence.note)}</p>`;
  }

  function selectUnit(name, navigate = true) {
    const unit = data.priorityIslands.find((item) => item.island === name);
    if (!unit) return;
    const level = MARKER_GROUPS.findIndex((group) => group.test(unit));
    document.getElementById("island-select").value = name;
    document.getElementById("unit-title").textContent = `${unit.island} — rank ${unit.rank} of ${data.priorityIslands.length}`;
    document.getElementById("unit-cover").textContent = `${fmt(unit.lcc)}% (${unit.surveyYear})`;

    const prediction = document.getElementById("unit-prediction");
    prediction.textContent = changeText(unit.predictedNextChange);
    prediction.title = `Range: ${fmt(unit.predictionLower, 1)} to ${fmt(unit.predictionUpper, 1)} pp/yr`;
    prediction.style.color = unit.predictedNextChange < 0 ? "#DC2626" : "#059669";

    document.getElementById("unit-urgency").innerHTML =
      `<span class="urgency-pill" style="background:${MARKER_GROUPS[level].color}" title="${MARKER_GROUPS[level].label}">${URGENCY[level]}</span>`;

    const stress = unit.stress;
    document.getElementById("unit-insight").textContent = stress.insight;
    document.getElementById("unit-top-stressor").textContent = stress.reportReason.label;
    renderUnitEvidence(stress, unit.surveyYear);
    renderStressBreakdown(stress, unit.predictedNextChange);
    document.getElementById("unit-heat-note").textContent =
      `Regional heat (NOAA): max DHW ${fmt(unit.dhwContext, 1)} °C-weeks. Context only; not in the model.`;

    renderHistory(unit);
    if (navigate) document.querySelector('[data-tab="diagnostics"]').click();
  }

  function renderValidation() {
    document.getElementById("model-benchmark-table").innerHTML = data.validationByYear.map((row) => `
      <tr><td>${row.target_year}</td><td>${row.n}</td><td>${fmt(row.mae, 2)}</td><td>${fmt(row.r2, 2)}</td><td>${fmt(row.bias, 2)}</td></tr>`).join("");
    const metrics = data.modelMetrics;
    document.getElementById("model-note").textContent = `${metrics.best_candidate} improves MAE ${fmt(metrics.mae_improvement_pct, 1)}% over the mean baseline with strong stability across all five evaluated target years.`;
  }

  // Evidence figures: numbers in the captions come from the data bundle so they
  // follow a retrain; clicking a figure opens it full size.
  function renderEvidence() {
    const metrics = data.modelMetrics;
    const set = (id, text) => { document.getElementById(id).textContent = text; };
    set("ev-paired-units", kpi.pairedUnits);
    set("ev-paired-change", `${fmt(kpi.pairedChange2024To2025, 2)}`.replace("-", "−"));
    set("ev-latest-mean", fmt(kpi.latestMeanCoralCover));
    set("ev-best-mae", fmt(metrics.best_mae, 3));
    set("ev-baseline-mae", fmt(metrics.baseline_mae, 3));
    set("ev-improvement", fmt(metrics.mae_improvement_pct, 1));
    set("ev-eval-obs", Number(metrics.evaluation_observations).toLocaleString("en-US"));

    const lightbox = document.getElementById("figure-lightbox");
    const close = () => lightbox.classList.remove("open");
    document.querySelectorAll("#tab-science .figure-img-wrapper").forEach((button) => {
      button.addEventListener("click", () => {
        const img = button.querySelector("img");
        document.getElementById("lightbox-img").src = img.src;
        document.getElementById("lightbox-img").alt = img.alt;
        document.getElementById("lightbox-title").textContent = button.dataset.title;
        lightbox.classList.add("open");
        document.getElementById("lightbox-close").focus();
      });
    });
    document.getElementById("lightbox-close").addEventListener("click", close);
    lightbox.addEventListener("click", (event) => { if (event.target === lightbox) close(); });
    document.addEventListener("keydown", (event) => { if (event.key === "Escape") close(); });
  }

  const select = document.getElementById("island-select");
  select.innerHTML = data.priorityIslands.map((unit) => `<option value="${escapeHtml(unit.island)}">${escapeHtml(unit.island)} — rank ${unit.rank}</option>`).join("");
  select.addEventListener("change", () => selectUnit(select.value));

  renderMap();
  renderQueue();
  renderReefEconomy();
  renderReefPotential();
  renderSeasonRest();
  renderValidation();
  renderEvidence();
  const initial = data.priorityIslands[0];
  if (initial) selectUnit(initial.island, false);
}());
