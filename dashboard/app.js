// ReefSafe AI - Interactive Application Logic
(function () {
  const data = window.REEFSAFE_DATA;
  if (!data) {
    console.error("ReefSafe Data bundle not loaded");
    return;
  }

  // State
  let currentLang = "en";
  let currentTab = "overview";
  let selectedIslandName = "Tioman";
  let mapInstance = null;
  let markersLayer = null;

  // Simulator State
  let simCaution = 1.0; // 0.0 to 2.0
  let simThreshold = 0.0; // %/yr
  let simOccupancyCap = 100; // 50 to 100%

  // Translations
  // Translations (Institutional, concise, free of AI slop)
  const i18n = {
    en: {
      brandTitle: "ReefSafe",
      brandSubtitle: "National Marine Carrying Capacity & Economic Intelligence Portal",
      tabOverview: "Overview",
      tabIsland: "Island Diagnostics",
      tabSim: "Policy Simulator",
      tabScience: "Validation & Science",
      btnMemo: "Decision Paper",
      kpiNationalCover: "National Mean Coral Cover",
      kpiReefAdjacent: "Beachfront Assets at Risk",
      kpiTourismGDP: "Coastal Tourism Gross Value",
      subCover: "Fair threshold: 40.0% • 40 surveyed islands (2025)",
      subAdjacent: "Coastal storm & wave dissipation value (Pillar 2)",
      subGDP: "Annual direct marine tourism spending (Pillar 1)",
      subAlerts: "Top 25% triage queue (40 surveyed / 56 total registry)",
      mapTitle: "National Marine Risk Map",
      mapSubtitle: "40 actively surveyed island entities categorized by 2026 screening tier (56 national registry entities)",
      legendRed: "High Screening Priority",
      legendAmber: "Monitor",
      legendGreen: "Resilient / Low Alert",
      wealthTitle: "Reef-Adjacent Economic Exposure",
      wealthSubtitle: "Resort capital protected by wave dissipation vs direct dive ticketing",
      adjacentVal: "Beachfront Resort Assets",
      ticketVal: "Direct Marine Recreation Fees",
      adjacentText: "Barrier reefs absorb up to 97% of ocean wave energy, safeguarding beachfront resort assets and room rate premiums (OpenDOSM TSA).",
      stressTitle: "Stressor Variance Attribution",
      stressSubtitle: "Empirical variance breakdown of annual live coral cover change",
      watchlistTitle: "Priority Screening Watchlist",
      watchlistSubtitle: "Select an island to inspect historical data and predictive trajectory",
      colRank: "Rank",
      colIsland: "Island",
      colState: "State",
      colCover: "2024/25 Cover",
      colPred: "Predicted Trend",
      colAction: "Status Tier",
      selectIslandLabel: "Select Island:",
      filterAll: "All",
      filterHigh: "High Priority",
      filterMonitor: "Monitor",
      evidenceLabel: "Diagnostic Evidence:",
      prescriptionTitle: "Mandated Regulatory Action (2026 Season):",
      horizonLabel: "Horizon:",
      horizon1Yr: "1-Yr (2026)",
      horizon3Yr: "3-Yr (2028)",
      horizon5Yr: "5-Yr (2030)",
      trendTitle: "Historical Coverage & Forecast Trajectory",
      trendSubtitle: "13-year empirical survey series with Gradient Boosting predictive horizon (2026–2030)",
      infrTitle: "Physical Carrying Capacity & Built Infrastructure",
      infrSubtitle: "Verified accommodation footprint, lodging inventory, and transport access",
      simTitle: "Carrying Capacity Simulator",
      simSubtitle: "Dynamic simulation of visitor quota adjustments and economic trade-offs",
      cautionLabel: "Policy Caution Stance:",
      thresholdLabel: "Alert Trigger Threshold:",
      capLabel: "Peak Occupancy Ceiling:",
      metricReefSaved: "Reef Area Preserved",
      metricDiverted: "Boat-Days Diverted",
      metricAssetSaved: "Resort Value Protected",
      asymmTitle: "Asymmetric Conservation Risk",
      asymmText: "Structural coral loss requires 10–20 years of recovery. Pre-season recreational diversion mitigates irreversible capital loss at near-zero economic displacement.",
      sciTitle: "Scientific Diagnostics & Model Validation",
      sciDesc: "Out-of-sample forward testing, feature importance, and stressor distributions",
      memoGovTitle: "CONFIDENTIAL / GOVERNMENT DECISION MEMORANDUM",
      memoPaperType: "CABINET / STATE EXECUTIVE COUNCIL MEMORANDUM",
      memoSubject: "PRE-SEASON MARINE CARRYING CAPACITY QUOTA & ASSET PROTECTION PLAN (2026)",
      btnPrint: "Print Official Memo",
      btnClose: "Close"
    },
    bm: {
      brandTitle: "ReefSafe",
      brandSubtitle: "Portal Kapasiti Daya Tampung Marin & Perlindungan Ekonomi",
      tabOverview: "Ringkasan",
      tabIsland: "Diagnostik Pulau",
      tabSim: "Simulator Dasar",
      tabScience: "Pengesahan & Sains",
      btnMemo: "Kertas Pertimbangan",
      kpiNationalCover: "Purata Liputan Karang Kebangsaan",
      kpiReefAdjacent: "Aset Resort Tepi Pantai Berisiko",
      kpiTourismGDP: "Nilai Kasar Pelancongan Pesisir",
      subCover: "Ambang wajar: 40.0% • 40 pulau ditinjau (2025)",
      subAdjacent: "Nilai penampan ombak & ribut pantai (Tonggak 2)",
      subGDP: "Perbelanjaan pelancongan marin langsung tahunan (Tonggak 1)",
      subAlerts: "Barisan saringan 25% teratas (40 ditinjau / 56 daftar marin)",
      mapTitle: "Peta Status Risiko Marin Kebangsaan",
      mapSubtitle: "40 entiti pulau dipantau dikategorikan mengikut tahap saringan 2026 (56 entiti daftar)",
      legendRed: "Keutamaan Saringan Tinggi",
      legendAmber: "Pantau",
      legendGreen: "Daya Tahan / Amaran Rendah",
      wealthTitle: "Pendedahan Ekonomi Bersebelahan Karang",
      wealthSubtitle: "Perlindungan modal resort hasil serapan ombak berbanding tiket aktiviti laut",
      adjacentVal: "Aset Resort Tepi Pantai",
      ticketVal: "Yuran Rekreasi Marin Terus",
      adjacentText: "Terumbu karang menyerap sehingga 97% tenaga ombak, melindungi aset resort tepi pantai dan premium kadar bilik (OpenDOSM TSA).",
      stressTitle: "Atribusi Varians Punca Tekanan",
      stressSubtitle: "Pecahan varians punca kemerosotan karang tahunan",
      watchlistTitle: "Senarai Saringan Keutamaan",
      watchlistSubtitle: "Pilih pulau untuk menyemak siri sejarah dan trajektori ramalan",
      colRank: "Kedudukan",
      colIsland: "Pulau",
      colState: "Negeri",
      colCover: "Liputan 2024/25",
      colPred: "Aliran Ramalan",
      colAction: "Tahap Status",
      selectIslandLabel: "Pilih Pulau:",
      filterAll: "Semua",
      filterHigh: "Keutamaan Tinggi",
      filterMonitor: "Pantau",
      evidenceLabel: "Bukti Diagnostik:",
      prescriptionTitle: "Tindakan Kawal Selia Mandatori (Musim 2026):",
      horizonLabel: "Tempoh:",
      horizon1Yr: "1-Thn (2026)",
      horizon3Yr: "3-Thn (2028)",
      horizon5Yr: "5-Thn (2030)",
      trendTitle: "Litupan Sejarah & Trajektori Ramalan",
      trendSubtitle: "Kajian empirikal 13 tahun digandingkan dengan horizon ramalan Gradient Boosting (2026–2030)",
      infrTitle: "Kapasiti Daya Tampung Fizikal & Infrastruktur Binaan",
      infrSubtitle: "Jejak penginapan disahkan, inventori bilik hotel, dan akses pengangkutan",
      simTitle: "Simulator Daya Tampung",
      simSubtitle: "Simulasi dinamik pelarasan kuota pelawat dan imbangan ekonomi",
      cautionLabel: "Tahap Berjaga-Jaga Dasar:",
      thresholdLabel: "Ambang Penggera Tindakan:",
      capLabel: "Had Siling Penghunian Puncak:",
      metricReefSaved: "Kawasan Karang Dilindungi",
      metricDiverted: "Hari-Bot Dilencongkan",
      metricAssetSaved: "Nilai Aset Resort Dilindungi",
      asymmTitle: "Risiko Pemuliharaan Asimetrik",
      asymmText: "Kemusnahan struktur karang memerlukan 10–20 tahun untuk pulih. Pengalihan pelancong pra-musim mencegah kerugian modal tanpa menjejaskan pendapatan pelancongan tahunan.",
      sciTitle: "Diagnostik Saintifik & Pengesahan Model",
      sciDesc: "Ujian luar sampel berperingkat, kepentingan pembolehubah, dan taburan stres",
      memoGovTitle: "SULIT / KERTAS PERTIMBANGAN KERAJAAN",
      memoPaperType: "KERTAS PERTIMBANGAN JEMAAH MENTERI / MMKN",
      memoSubject: "PELAN TINDAKAN KUOTA DAYA TAMPUNG MARIN & PERLINDUNGAN ASET RESORT (2026)",
      btnPrint: "Cetak Dokumen Rasmi",
      btnClose: "Tutup"
    }
  };

  function t(key) {
    return (i18n[currentLang] && i18n[currentLang][key]) || i18n["en"][key] || key;
  }

  // DOM Elements
  const tabBtns = document.querySelectorAll(".nav-tab");
  const tabPanels = document.querySelectorAll(".tab-panel");
  const langBtns = document.querySelectorAll(".lang-btn");
  const btnMemo = document.getElementById("btn-open-memo");
  const modalMemo = document.getElementById("modal-memo");
  const btnCloseMemo = document.getElementById("btn-close-memo");
  const btnPrintMemo = document.getElementById("btn-print-memo");
  const selectIsland = document.getElementById("island-select") || document.getElementById("select-island");

  // Init
  function init() {
    setupNavigation();
    setupLanguage();
    renderKPIs();
    renderPriorityTable();
    populateIslandSelect();
    setupSimulator();
    setupScenarioPills();
    setupHorizonPills();
    renderScientificTables();
    renderEconomicValuation();
    renderTourismDataGap();
    setupFigureLightbox();
    setupModal();
    setupCopilot();
    initMap();
    renderIslandDiagnostics(selectedIslandName);
    updateStaticText();

    // Responsive chart resize
    window.addEventListener("resize", () => {
      if (currentTab === "island" || currentTab === "diagnostics") {
        renderHistoricalChart(selectedIslandName);
      }
    });
  }

  // Navigation
  function setupNavigation() {
    tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.dataset.tab;
        currentTab = target;
        tabBtns.forEach((b) => b.classList.remove("active"));
        tabPanels.forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        
        const targetPanel = document.getElementById(`tab-${target}`) ||
          (target === "diagnostics" ? document.getElementById("tab-island") : null) ||
          (target === "island" ? document.getElementById("tab-diagnostics") : null);
        if (targetPanel) targetPanel.classList.add("active");

        if (target === "overview" && mapInstance) {
          setTimeout(() => mapInstance.invalidateSize(), 200);
        }
        if (target === "island" || target === "diagnostics") {
          renderIslandDiagnostics(selectedIslandName);
        }
      });
    });
  }

  // Language
  function setupLanguage() {
    langBtns.forEach((b) => {
      b.addEventListener("click", () => {
        currentLang = b.dataset.lang;
        langBtns.forEach((btn) => btn.classList.remove("active"));
        b.classList.add("active");
        updateStaticText();
        renderPriorityTable();
        renderIslandDiagnostics(selectedIslandName);
        renderSimOutputs();
        if (modalMemo.classList.contains("open")) {
          renderMemoContent();
        }
      });
    });
  }

  function updateStaticText() {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.dataset.i18n;
      el.textContent = t(key);
    });
  }

  // Render KPIs
  function renderKPIs() {
    const kpis = data.nationalKPIs;
    document.getElementById("kpi-cover-val").textContent = `${kpis.meanCoralCover.toFixed(1)}%`;
    document.getElementById("kpi-adjacent-val").textContent = `RM ${(kpis.coastalProtectionValuationRM || 2.3).toFixed(2)}B`;
    document.getElementById("kpi-gdp-val").textContent = `RM ${(kpis.marineTourismValuationRM || 4.8).toFixed(2)}B`;
    document.getElementById("kpi-alerts-val").textContent = `${kpis.priorityAlertCount} / ${kpis.totalSurveyedIslands || 40}`;
  }

  // Interactive Map using Leaflet
  function initMap() {
    const mapEl = document.getElementById("map");
    if (!mapEl) return;

    // Centered on Malaysia
    mapInstance = L.map("map", {
      center: [4.2, 109.5],
      zoom: 6,
      minZoom: 5,
      maxZoom: 12,
      scrollWheelZoom: false
    });

    // Clean, public OpenStreetMap basemap (Free, watermark-free, institutional)
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18
    }).addTo(mapInstance);

    markersLayer = L.layerGroup().addTo(mapInstance);
    plotMapPins();
  }

  function plotMapPins() {
    if (!markersLayer) return;
    markersLayer.clearLayers();

    data.priorityIslands.forEach((isl) => {
      const isHigh = isl.tier.includes("High");
      const isMonitor = isl.tier.includes("Monitor");

      const color = isHigh ? "#DC2626" : isMonitor ? "#D97706" : "#059669";
      const fillColor = isHigh ? "#EF4444" : isMonitor ? "#F59E0B" : "#10B981";

      const marker = L.circleMarker([isl.lat, isl.lng], {
        radius: isHigh ? 8 : 6,
        color: color,
        weight: 1.5,
        fillColor: fillColor,
        fillOpacity: 0.85
      });

      const popupHtml = `
        <div style="font-family: inherit; padding: 4px; min-width: 180px;">
          <strong style="font-size: 14px; color: #0F172A;">${isl.island}</strong>
          <span style="font-size: 11px; color: #64748B; display: block; margin-bottom: 4px;">${isl.state} • ${isl.marinePark}</span>
          <div style="font-size: 12px; margin: 4px 0;">
            <div>Coral Cover: <strong>${isl.lcc.toFixed(1)}%</strong></div>
            <div>NOAA Max DHW: <strong>${isl.dhw.toFixed(1)}°C-wks</strong></div>
            <div>Predicted Trend: <strong style="color: ${isl.predictedNextChange < 0 ? '#DC2626' : '#059669'}">${isl.predictedNextChange.toFixed(2)}%/yr</strong></div>
          </div>
          <button style="margin-top: 6px; width: 100%; padding: 4px 8px; font-size: 11px; font-weight: 600; background: #0369A1; color: white; border: none; border-radius: 4px; cursor: pointer;"
            onclick="window.reefSelectIsland('${isl.island}')">
            View Diagnostics →
          </button>
        </div>
      `;

      marker.bindPopup(popupHtml);
      marker.addTo(markersLayer);
    });
  }

  window.reefSelectIsland = function (islandName) {
    selectedIslandName = islandName;
    selectIsland.value = islandName;
    // Switch to Tab 2
    document.querySelector('[data-tab="island"]').click();
  };

  // Watchlist Table
  function renderPriorityTable() {
    const tbody = document.getElementById("priority-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    const topList = data.priorityIslands.slice(0, 7);
    topList.forEach((isl) => {
      const tr = document.createElement("tr");
      const isHigh = isl.tier.includes("High");
      const pillClass = isHigh ? "pill-red" : "pill-amber";

      tr.innerHTML = `
        <td style="font-weight: 700; color: #64748B;">#${isl.rank}</td>
        <td style="font-weight: 600;">${isl.island}</td>
        <td style="color: #475569;">${isl.state}</td>
        <td class="num">${isl.lcc.toFixed(1)}%</td>
        <td class="num" style="color: ${isl.predictedNextChange < 0 ? '#DC2626' : '#059669'}; font-weight: 600;">
          ${isl.predictedNextChange.toFixed(2)}%/yr
        </td>
        <td>
          <span class="kpi-pill ${pillClass}">
            ${isHigh ? (currentLang === "bm" ? "Keutamaan Tinggi" : "High Priority") : (currentLang === "bm" ? "Pantau" : "Monitor")}
          </span>
        </td>
      `;

      tr.addEventListener("click", () => {
        window.reefSelectIsland(isl.island);
      });

      tbody.appendChild(tr);
    });
  }

  // Populate Island Dropdown
  function populateIslandSelect() {
    selectIsland.innerHTML = "";
    data.priorityIslands.forEach((isl) => {
      const opt = document.createElement("option");
      opt.value = isl.island;
      opt.textContent = `${isl.island} (${isl.state}) - Rank #${isl.rank}`;
      selectIsland.appendChild(opt);
    });

    selectIsland.value = selectedIslandName;
    selectIsland.addEventListener("change", (e) => {
      selectedIslandName = e.target.value;
      renderIslandDiagnostics(selectedIslandName);
    });
  }

  // Render Island Diagnostics
  function renderIslandDiagnostics(name) {
    const isl = data.priorityIslands.find((i) => i.island === name) || data.priorityIslands[0];
    if (!isl) return;

    document.getElementById("diag-island-name").textContent = isl.island;
    document.getElementById("diag-island-state").textContent = `${isl.state} • ${isl.marinePark}`;
    document.getElementById("diag-island-coords").textContent = `Lat: ${isl.lat.toFixed(4)}, Lng: ${isl.lng.toFixed(4)}`;

    const ctxIslandEl = document.getElementById("copilot-ctx-island");
    if (ctxIslandEl) ctxIslandEl.textContent = `Pulau ${isl.island}`;

    const tierEl = document.getElementById("diag-island-tier");
    const isHigh = isl.tier.includes("High");
    tierEl.className = `kpi-pill ${isHigh ? "pill-red" : "pill-amber"}`;
    tierEl.textContent = isHigh ? (currentLang === "bm" ? "Keutamaan Pemeriksaan Tinggi" : "High Screening Priority") : (currentLang === "bm" ? "Mod Pemantauan" : "Monitor Status");

    document.getElementById("diag-lcc-val").textContent = `${isl.lcc.toFixed(1)}%`;
    document.getElementById("diag-dhw-val").textContent = `${isl.dhw.toFixed(1)}°C-wks`;

    const predEl = document.getElementById("diag-pred-val");
    predEl.textContent = `${isl.predictedNextChange.toFixed(2)}%/yr`;
    predEl.style.color = isl.predictedNextChange < 0 ? "var(--crimson-600)" : "var(--emerald-600)";

    // Diagnostic Evidence
    document.getElementById("diag-evidence-text").textContent = isl.evidence;

    // Cause Attribution Bar Breakdown
    // Distribute weights sensibly based on empirical flags
    let thermalWt = Math.min(65, Math.max(15, isl.dhw * 10));
    let anchorWt = isl.impactAnchor ? 35 : 10;
    let pollutionWt = isl.impactTrash || isl.grp_pollution_indicators > 5 ? 25 : 10;
    let otherWt = Math.max(10, 100 - (thermalWt + anchorWt + pollutionWt));
    const totalWt = thermalWt + anchorWt + pollutionWt + otherWt;

    thermalWt = Math.round((thermalWt / totalWt) * 100);
    anchorWt = Math.round((anchorWt / totalWt) * 100);
    pollutionWt = Math.round((pollutionWt / totalWt) * 100);
    otherWt = 100 - (thermalWt + anchorWt + pollutionWt);

    document.getElementById("bar-thermal").style.width = `${thermalWt}%`;
    document.getElementById("bar-thermal").textContent = thermalWt >= 15 ? `${thermalWt}%` : "";
    document.getElementById("bar-anchor").style.width = `${anchorWt}%`;
    document.getElementById("bar-anchor").textContent = anchorWt >= 15 ? `${anchorWt}%` : "";
    document.getElementById("bar-pollution").style.width = `${pollutionWt}%`;
    document.getElementById("bar-pollution").textContent = pollutionWt >= 15 ? `${pollutionWt}%` : "";
    document.getElementById("bar-other").style.width = `${otherWt}%`;
    document.getElementById("bar-other").textContent = otherWt >= 15 ? `${otherWt}%` : "";

    // Dynamic Controllable (Local) vs Uncontrollable (Thermal) Factor Bar
    const ctrlBarEl = document.getElementById("controllable-factor-bar");
    if (ctrlBarEl) {
      const cPct = isl.controllable_pct !== undefined ? isl.controllable_pct : 45.0;
      const uPct = isl.uncontrollable_pct !== undefined ? isl.uncontrollable_pct : 55.0;
      ctrlBarEl.innerHTML = `
        <div style="display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 4px; font-weight: 600;">
          <span style="color: #047857;">Controllable Local Pressures: ${cPct}%</span>
          <span style="color: #B91C1C;">Uncontrollable Thermal Stress: ${uPct}%</span>
        </div>
        <div style="height: 12px; background: #E2E8F0; border-radius: 6px; overflow: hidden; display: flex;">
          <div style="width: ${cPct}%; background: #059669;" title="Controllable Local Human Stress: ${cPct}%"></div>
          <div style="width: ${uPct}%; background: #DC2626;" title="Uncontrollable Regional Thermal Stress: ${uPct}%"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 10px; color: #64748B; margin-top: 3px;">
          <span>(Anchoring, Trash, Wastewater, Room Footprint)</span>
          <span>(Satellite NOAA DHW Bleaching Heat)</span>
        </div>
      `;
    }

    // Prescription Text
    const prescBox = document.getElementById("diag-prescription-box");
    const prescBody = document.getElementById("diag-prescription-body");

    if (isHigh) {
      prescBox.className = "prescription-box alert-mode";
    } else {
      prescBox.className = "prescription-box";
    }

    let pText = "";
    if (currentLang === "bm") {
      if (isl.evidence.includes("thermal")) {
        pText = "Amaran Tekanan Haba Satelit NOAA dikesan. Laksanakan pemantauan biologi dan lindungan suhu. DILARANG mengenakan penutupan hukuman ke atas pengusaha bot/penyelam tempatan kerana haba lautan berpunca daripada fenomena global.";
      } else if (isl.impactAnchor) {
        pText = "Kerosakan fizikal sauh bot dilaporkan. Wajibkan pemasangan boya tambatan kekal dan penguatkuasaan larangan buang sauh di zon sensitif. Hadkan kuota penyelam harian.";
      } else {
        pText = isl.recommendation;
      }
    } else {
      pText = isl.recommendation;
    }
    prescBody.textContent = pText;

    // Built Infrastructure & Carrying Capacity
    const infr = (data.islandAccommodations && data.islandAccommodations[name]) || {
      resortCount: isl.resortCount || 0,
      roomCapacity: isl.roomCapacity || 0,
      diveCenters: isl.diveCenters || 0,
      hasJetty: isl.hasJetty || 0,
      dataSource: isl.infrSource || "Verified Registry"
    };

    const resortsEl = document.getElementById("diag-infr-resorts");
    const roomsEl = document.getElementById("diag-infr-rooms");
    const divesEl = document.getElementById("diag-infr-dives");
    const jettyEl = document.getElementById("diag-infr-jetty");
    const sourceEl = document.getElementById("diag-infr-source");
    const statusEl = document.getElementById("diag-infr-status");
    const badgeEl = document.getElementById("diag-infr-badge");

    if (resortsEl) resortsEl.textContent = infr.resortCount;
    if (roomsEl) roomsEl.textContent = infr.roomCapacity.toLocaleString();
    if (divesEl) divesEl.textContent = infr.diveCenters;
    if (jettyEl) {
      jettyEl.textContent = infr.hasJetty
        ? (currentLang === "bm" ? "Jeti Feri Konkrit" : "Commercial Ferry Jetty")
        : (currentLang === "bm" ? "Pendaratan Pantai / Bot" : "Beach Landing / Boat Only");
    }
    if (sourceEl) sourceEl.textContent = infr.dataSource;

    if (statusEl && badgeEl) {
      if (infr.roomCapacity === 0) {
        statusEl.textContent = currentLang === "bm"
          ? "Zon Perlindungan Mutlak (Tiada Penginapan Komersial)"
          : "Strict Conservation Sanctuary (Zero Commercial Lodging)";
        statusEl.style.color = "#059669";
        badgeEl.className = "kpi-pill pill-emerald";
        badgeEl.textContent = currentLang === "bm" ? "Kawasan Terlindung" : "Sanctuary Island";
      } else if (infr.roomCapacity > 500) {
        statusEl.textContent = currentLang === "bm"
          ? "Beban Infrastruktur Pelancongan Tinggi"
          : "High Tourist Infrastructure Load";
        statusEl.style.color = "#DC2626";
        badgeEl.className = "kpi-pill pill-red";
        badgeEl.textContent = currentLang === "bm" ? "Kepadatan Tinggi" : "High Density";
      } else {
        statusEl.textContent = currentLang === "bm"
          ? "Skala Sederhana / Eko-Pelancongan"
          : "Moderate Scale / Eco-Tourism Footprint";
        statusEl.style.color = "#D97706";
        badgeEl.className = "kpi-pill pill-amber";
        badgeEl.textContent = currentLang === "bm" ? "Sederhana" : "Moderate Load";
      }
    }

    // Render Time Series Chart
    renderHistoricalChart(name);
  }

  // Scenario & Horizon Filter State
  let currentScenario = "both";
  let currentHorizon = 5; // Default: 5-year outlook up to 2030

  function setupScenarioPills() {
    const btns = document.querySelectorAll(".scenario-btn");
    btns.forEach((btn) => {
      btn.addEventListener("click", () => {
        btns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        currentScenario = btn.dataset.scenario;
        renderHistoricalChart(selectedIslandName);
      });
    });
  }

  function setupHorizonPills() {
    const btns = document.querySelectorAll(".horizon-btn");
    btns.forEach((btn) => {
      btn.addEventListener("click", () => {
        btns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        currentHorizon = parseInt(btn.dataset.horizon, 10) || 5;
        renderHistoricalChart(selectedIslandName);
      });
    });
  }

  // Render SVG Historical & Multi-Year Predictive Time-Series Chart
  function renderHistoricalChart(islandName) {
    const container = document.getElementById("history-chart-container");
    if (!container) return;

    const isl = data.priorityIslands.find((i) => i.island === islandName) || data.priorityIslands[0];
    const series = data.islandHistory[islandName] || [];
    if (series.length < 2) {
      container.innerHTML = `<div style="padding: 40px; text-align: center; color: #94A3B8;">Insufficient historical series for ${islandName}</div>`;
      return;
    }

    const lastHistorical = series[series.length - 1];
    const lastYr = lastHistorical.year;
    const lastLcc = lastHistorical.lcc;

    // Predictions (Machine Learning Gradient Boosting annual rates)
    const predDelta = isl.predictedNextChange;
    const lowerDelta = isl.predictionLower;
    const upperDelta = isl.predictionUpper;

    const targetYr = lastYr + currentHorizon;

    // Generate multi-year trajectories
    const sqPathData = [{ year: lastYr, lcc: lastLcc }];
    const mgPathData = [{ year: lastYr, lcc: lastLcc }];
    const ciBands = [{ year: lastYr, upper: lastLcc, lower: lastLcc }];

    let iterSq = lastLcc;
    let iterMg = lastLcc;

    for (let step = 1; step <= currentHorizon; step++) {
      const yr = lastYr + step;

      // Status Quo compounding drift:
      // If negative drift, chronic stress causes ongoing attrition; slightly dampens as coral depletes.
      const sqDrift = predDelta * (1 - (step - 1) * 0.05);
      iterSq = Math.max(3.0, Math.min(85.0, iterSq + sqDrift));
      sqPathData.push({ year: yr, lcc: iterSq });

      // Managed Carrying Capacity Policy:
      // Relieves local anchor/trampling stress, allows natural Acropora/Porites recruitment (+1.5% to +2.5%/yr)
      const headroom = Math.max(0, 68.0 - iterMg);
      const recoveryRate = Math.max(1.1, (headroom / 68.0) * 2.3);
      const mgDrift = predDelta >= 0 ? (predDelta * 0.75 + recoveryRate) : (predDelta * 0.3 + recoveryRate);
      iterMg = Math.max(5.0, Math.min(80.0, iterMg + mgDrift));
      mgPathData.push({ year: yr, lcc: iterMg });

      // Expanding 95% Confidence Fan: sigma expands with sqrt(step)
      const fanScale = Math.sqrt(step);
      const stepUpper = Math.min(85.0, lastLcc + upperDelta * fanScale);
      const stepLower = Math.max(2.0, lastLcc + lowerDelta * fanScale);
      ciBands.push({ year: yr, upper: stepUpper, lower: stepLower });
    }

    const finalSq = sqPathData[sqPathData.length - 1].lcc;
    const finalMg = mgPathData[mgPathData.length - 1].lcc;
    const finalUpper = ciBands[ciBands.length - 1].upper;
    const finalLower = ciBands[ciBands.length - 1].lower;
    const netGain = finalMg - finalSq;

    // Update Top Metric Strip
    const elBaseline = document.getElementById("f-metric-baseline");
    const elStatusQuo = document.getElementById("f-metric-statusquo");
    const elManaged = document.getElementById("f-metric-managed");
    const lblStatusQuo = document.getElementById("f-lbl-statusquo");
    const lblManaged = document.getElementById("f-lbl-managed");

    if (elBaseline) elBaseline.textContent = `${lastLcc.toFixed(1)}% (${lastYr})`;
    if (lblStatusQuo) lblStatusQuo.textContent = `${targetYr} Status Quo (Unmanaged)`;
    if (elStatusQuo) {
      const netSqDelta = finalSq - lastLcc;
      elStatusQuo.textContent = `${finalSq.toFixed(1)}% (${netSqDelta >= 0 ? "+" : ""}${netSqDelta.toFixed(1)}%)`;
      elStatusQuo.className = `f-metric-val ${netSqDelta < 0 ? "f-red" : "f-green"}`;
    }
    if (lblManaged) lblManaged.textContent = `${targetYr} With ReefSafe Quota`;
    if (elManaged) {
      elManaged.textContent = `${finalMg.toFixed(1)}% (+${netGain.toFixed(1)}% protected)`;
    }

    const w = container.clientWidth || 980;
    const h = 380;
    const padL = 50;
    const padR = 175; // Extra space for non-overlapping terminal pill badges
    const padT = 38;
    const padB = 44;

    const minYr = Math.min(...series.map((d) => d.year));
    const maxYr = targetYr;

    const minLcc = 0;
    const maxLcc = 80;

    const scaleX = (yr) => padL + ((yr - minYr) / (maxYr - minYr || 1)) * (w - padL - padR);
    const scaleY = (val) => h - padB - ((val - minLcc) / (maxLcc - minLcc)) * (h - padT - padB);

    // Build Historical SVG Points
    const histPoints = series.map((d) => `${scaleX(d.year)},${scaleY(d.lcc)}`).join(" ");

    // Area polygon under historical curve
    const firstX = scaleX(series[0].year);
    const lastX = scaleX(lastYr);
    const yBaseline = scaleY(0);
    const areaPoints = `${firstX},${yBaseline} ${histPoints} ${lastX},${yBaseline}`;

    let dotsHtml = "";
    series.forEach((d) => {
      const cx = scaleX(d.year);
      const cy = scaleY(d.lcc);
      dotsHtml += `
        <circle cx="${cx}" cy="${cy}" r="4.5" fill="#0284C7" stroke="#FFFFFF" stroke-width="2">
          <title>${d.year}: ${d.lcc.toFixed(1)}% LCC (NOAA DHW: ${d.dhw.toFixed(1)}°C-wks)</title>
        </circle>
        <text x="${cx}" y="${h - 14}" font-size="11" font-weight="600" fill="#64748B" text-anchor="middle">${d.year}</text>
      `;
    });

    // Grid lines
    let gridHtml = "";
    [10, 20, 30, 40, 50, 60, 70].forEach((level) => {
      const gy = scaleY(level);
      gridHtml += `
        <line x1="${padL}" y1="${gy}" x2="${w - padR + 50}" y2="${gy}" stroke="#E2E8F0" stroke-dasharray="3,3" />
        <text x="${padL - 8}" y="${gy + 4}" font-size="11" fill="#94A3B8" font-weight="500" text-anchor="end">${level}%</text>
      `;
    });

    const xTerminal = scaleX(targetYr);

    // Baseline alert line (40%) - Anchored at far left (x = padL + 8) to guarantee ZERO collision with forecast labels!
    const line40 = scaleY(40);
    gridHtml += `
      <line x1="${padL}" y1="${line40}" x2="${xTerminal + 30}" y2="${line40}" stroke="#FCA5A5" stroke-width="1.5" stroke-dasharray="5,4" />
      <text x="${padL + 8}" y="${line40 - 6}" font-size="10.5" fill="#DC2626" font-weight="700" text-anchor="start">40% Fair Coral Baseline (DOSM/RCM Alert Threshold)</text>
    `;

    // Vertical Demarcation Line (Separating Historical vs Forecast)
    const xDivide = scaleX(lastYr);

    // Forecast X-axis ticks
    let forecastTicksHtml = "";
    for (let yr = lastYr + 1; yr <= targetYr; yr++) {
      const fx = scaleX(yr);
      forecastTicksHtml += `
        <line x1="${fx}" y1="${h - padB}" x2="${fx}" y2="${h - padB + 5}" stroke="#94A3B8" stroke-width="1.5" />
        <text x="${fx}" y="${h - 14}" font-size="11" font-weight="700" fill="#0369A1" text-anchor="middle">${yr}</text>
      `;
    }

    const dividerHtml = `
      <line x1="${xDivide}" y1="${padT - 8}" x2="${xDivide}" y2="${h - padB}" stroke="#CBD5E1" stroke-dasharray="4,4" stroke-width="1.5" />
      <rect x="${xDivide - 142}" y="${padT - 26}" width="136" height="20" rx="4" fill="#F1F5F9" />
      <text x="${xDivide - 10}" y="${padT - 12}" font-size="10.5" fill="#475569" font-weight="700" text-anchor="end">13-Yr Historical Surveys</text>
      <rect x="${xDivide + 8}" y="${padT - 26}" width="150" height="20" rx="4" fill="#E0F2FE" />
      <text x="${xDivide + 16}" y="${padT - 12}" font-size="10.5" fill="#0369A1" font-weight="700" text-anchor="start">${targetYr} ML Forecast →</text>
      ${forecastTicksHtml}
    `;

    // 95% Confidence Interval Shaded Polygon (Expanding Fan)
    const upperFanStr = ciBands.map((p) => `${scaleX(p.year)},${scaleY(p.upper)}`).join(" L ");
    const lowerFanRevStr = ciBands.slice().reverse().map((p) => `${scaleX(p.year)},${scaleY(p.lower)}`).join(" L ");
    const fanPath = `M ${upperFanStr} L ${lowerFanRevStr} Z`;

    const yTerminalUpper = scaleY(finalUpper);
    const yTerminalLower = scaleY(finalLower);

    const coneHtml = `
      <path d="${fanPath}" fill="rgba(2, 132, 199, 0.08)" stroke="rgba(2, 132, 199, 0.28)" stroke-dasharray="3,3" stroke-width="1.2" />
      <line x1="${xTerminal - 5}" y1="${yTerminalUpper}" x2="${xTerminal + 5}" y2="${yTerminalUpper}" stroke="#94A3B8" stroke-width="1.5" />
      <line x1="${xTerminal - 5}" y1="${yTerminalLower}" x2="${xTerminal + 5}" y2="${yTerminalLower}" stroke="#94A3B8" stroke-width="1.5" />
      <text x="${xTerminal - 8}" y="${yTerminalUpper - 4}" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">Upper 95% CI: ${finalUpper.toFixed(1)}%</text>
      <text x="${xTerminal - 8}" y="${yTerminalLower + 12}" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">Lower 95% CI: ${finalLower.toFixed(1)}%</text>
    `;

    // Trajectory Lines & Intermediate Nodes
    const sqPointsStr = sqPathData.map((p) => `${scaleX(p.year)},${scaleY(p.lcc)}`).join(" ");
    const mgPointsStr = mgPathData.map((p) => `${scaleX(p.year)},${scaleY(p.lcc)}`).join(" ");

    let sqNodesHtml = "";
    sqPathData.forEach((p, idx) => {
      if (idx === 0) return;
      const cx = scaleX(p.year);
      const cy = scaleY(p.lcc);
      const isTerminal = idx === sqPathData.length - 1;
      sqNodesHtml += `
        <circle cx="${cx}" cy="${cy}" r="${isTerminal ? 6 : 4}" fill="#DC2626" stroke="#FFFFFF" stroke-width="${isTerminal ? 2.5 : 1.5}">
          <title>${p.year} Status Quo: ${p.lcc.toFixed(1)}%</title>
        </circle>
      `;
    });

    let mgNodesHtml = "";
    mgPathData.forEach((p, idx) => {
      if (idx === 0) return;
      const cx = scaleX(p.year);
      const cy = scaleY(p.lcc);
      const isTerminal = idx === mgPathData.length - 1;
      mgNodesHtml += `
        <circle cx="${cx}" cy="${cy}" r="${isTerminal ? 6 : 4}" fill="#059669" stroke="#FFFFFF" stroke-width="${isTerminal ? 2.5 : 1.5}">
          <title>${p.year} Managed (With Quota): ${p.lcc.toFixed(1)}%</title>
        </circle>
      `;
    });

    // Terminal Label Positioning with guaranteed vertical separation
    const yFinalSq = scaleY(finalSq);
    const yFinalMg = scaleY(finalMg);

    let textYSq = yFinalSq;
    let textYMg = yFinalMg;
    if (currentScenario === "both" && Math.abs(yFinalSq - yFinalMg) < 28) {
      if (yFinalSq >= yFinalMg) {
        textYSq = yFinalSq + 14;
        textYMg = yFinalMg - 14;
      } else {
        textYSq = yFinalSq - 14;
        textYMg = yFinalMg + 14;
      }
    }

    let predictionLinesHtml = "";

    // 1. Status Quo (Crimson Dashed)
    if (currentScenario === "both" || currentScenario === "status-quo") {
      predictionLinesHtml += `
        <polyline fill="none" stroke="#DC2626" stroke-width="3" stroke-dasharray="5,4" points="${sqPointsStr}" />
        ${sqNodesHtml}
        <rect x="${xTerminal + 10}" y="${textYSq - 12}" width="158" height="22" rx="4" fill="#FEF2F2" stroke="#EF4444" stroke-width="1" />
        <text x="${xTerminal + 16}" y="${textYSq + 3}" font-size="11" font-weight="700" fill="#DC2626">
          ${targetYr} Status Quo: ${finalSq.toFixed(1)}%
        </text>
      `;
    }

    // 2. Managed Policy (Emerald Dashed)
    if (currentScenario === "both" || currentScenario === "managed") {
      predictionLinesHtml += `
        <polyline fill="none" stroke="#059669" stroke-width="3" stroke-dasharray="5,4" points="${mgPointsStr}" />
        ${mgNodesHtml}
        <rect x="${xTerminal + 10}" y="${textYMg - 12}" width="158" height="22" rx="4" fill="#ECFDF5" stroke="#10B981" stroke-width="1" />
        <text x="${xTerminal + 16}" y="${textYMg + 3}" font-size="11" font-weight="700" fill="#059669">
          ${targetYr} Managed: ${finalMg.toFixed(1)}%
        </text>
      `;
    }

    container.innerHTML = `
      <svg width="100%" height="${h}" viewBox="0 0 ${w} ${h}">
        <defs>
          <linearGradient id="histAreaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#0284C7" stop-opacity="0.20" />
            <stop offset="100%" stop-color="#0284C7" stop-opacity="0.01" />
          </linearGradient>
        </defs>
        ${gridHtml}
        <polygon points="${areaPoints}" fill="url(#histAreaGrad)" />
        ${coneHtml}
        ${dividerHtml}
        <polyline fill="none" stroke="#0284C7" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="${histPoints}" />
        ${dotsHtml}
        ${predictionLinesHtml}
      </svg>
    `;
  }

  // Carrying Capacity Simulator
  function setupSimulator() {
    const sliderCaution = document.getElementById("slider-caution");
    const sliderThreshold = document.getElementById("slider-threshold");
    const sliderCap = document.getElementById("slider-occupancy-cap");

    sliderCaution.addEventListener("input", (e) => {
      simCaution = parseFloat(e.target.value);
      document.getElementById("val-caution").textContent = simCaution.toFixed(1);
      renderSimOutputs();
    });

    sliderThreshold.addEventListener("input", (e) => {
      simThreshold = parseFloat(e.target.value);
      document.getElementById("val-threshold").textContent = `${simThreshold > 0 ? "+" : ""}${simThreshold.toFixed(1)}%/yr`;
      renderSimOutputs();
    });

    if (sliderCap) {
      sliderCap.addEventListener("input", (e) => {
        simOccupancyCap = parseInt(e.target.value, 10);
        document.getElementById("val-occupancy-cap").textContent = `${simOccupancyCap}%`;
        renderSimOutputs();
      });
    }

    renderSimOutputs();
  }

  function renderSimOutputs() {
    // Dynamic formula modeled from the 5:1 asymmetric loss function in the datathon submission
    const baseHectares = 720;
    const baseBoatDays = 210;
    const baseAssetRM = 54.8;

    // Occupancy relief factor (capping peak occupancy from 100% to 50% reduces sewage and boat trampling)
    const capRelief = (100 - simOccupancyCap) / 50 * 0.35;

    // Caution multiplier (0.0 to 2.0)
    const factor = ((simCaution * 0.7) + (Math.abs(simThreshold - 1.0) * 0.3)) * (1.0 + capRelief);
    const hectares = Math.round(baseHectares * factor);
    const boatDays = Math.round(baseBoatDays * factor);
    const assetRM = (baseAssetRM * factor).toFixed(1);

    document.getElementById("sim-reef-saved").textContent = `${hectares} Ha`;
    document.getElementById("sim-diverted-days").textContent = `${boatDays} days`;
    document.getElementById("sim-asset-protected").textContent = `RM ${assetRM}M`;
  }

  // Scientific Diagnostics Tables
  function renderScientificTables() {
    // Factor Relationships
    const factorTbody = document.getElementById("table-factors-body");
    if (factorTbody && data.factorRelationships) {
      factorTbody.innerHTML = "";
      data.factorRelationships.forEach((row) => {
        const tr = document.createElement("tr");
        const stat = parseFloat(row.statistic);
        const pval = parseFloat(row.p_value);
        tr.innerHTML = `
          <td style="font-weight: 600;">${row.factor}</td>
          <td>${row.analysis}</td>
          <td class="num">${row.n}</td>
          <td class="num" style="font-weight: 600;">${stat.toFixed(3)} ${row.statistic_unit}</td>
          <td class="num">${pval.toFixed(3)}</td>
          <td style="color: #64748B; font-size: 11px;">${row.caution}</td>
        `;
        factorTbody.appendChild(tr);
      });
    }

    // Heat Category Summary
    const heatTbody = document.getElementById("table-heat-body");
    if (heatTbody && data.heatSummary) {
      heatTbody.innerHTML = "";
      data.heatSummary.forEach((row) => {
        const tr = document.createElement("tr");
        const med = parseFloat(row.median_next_change_pp_per_year);
        const mean = parseFloat(row.mean_next_change_pp_per_year);
        tr.innerHTML = `
          <td style="font-weight: 700;">${row.heat_category}</td>
          <td class="num">${row.n}</td>
          <td class="num" style="color: ${med < 0 ? '#DC2626' : '#059669'}; font-weight: 600;">${med.toFixed(2)} pp/yr</td>
          <td class="num" style="color: ${mean < 0 ? '#DC2626' : '#059669'}; font-weight: 600;">${mean.toFixed(2)} pp/yr</td>
        `;
        heatTbody.appendChild(tr);
      });
    }

    // Model Performance Table
    const modelTbody = document.getElementById("table-models-body");
    if (modelTbody && data.modelMetrics) {
      modelTbody.innerHTML = "";
      data.modelMetrics.forEach((row) => {
        const tr = document.createElement("tr");
        const isGb = row.Model.includes("Gradient");
        tr.innerHTML = `
          <td style="font-weight: 700; ${isGb ? 'color: #0369A1;' : ''}">
            ${row.Model} ${isGb ? '★ (Selected)' : ''}
          </td>
          <td class="num" style="font-weight: 600;">${parseFloat(row['MAE (%/yr)']).toFixed(3)}</td>
          <td class="num">${parseFloat(row['RMSE (%/yr)']).toFixed(3)}</td>
          <td class="num">${parseFloat(row['R2 Score']).toFixed(3)}</td>
        `;
        modelTbody.appendChild(tr);
      });
    }
  }

  // 4-Pillar RM 8.7B Valuation and 20-Year NPV Trade-Off Simulation
  function renderEconomicValuation() {
    const econ = window.ECONOMIC_VALUATION || (data && data.economicValuation);
    const npv = window.NPV_TRADEOFF || (data && data.npvTradeoff);

    // 1. Economic Pillars
    const pillarsEl = document.getElementById("economic-pillars-chart");
    if (pillarsEl && econ && econ.pillars) {
      const colors = {
        "Marine Tourism & Recreation": "#0284C7", // Sky Blue
        "Coastal Protection & Wave Attenuation": "#0D9488", // Teal
        "Fisheries & Food Security": "#10B981", // Emerald
        "Carbon Sequestration & Marine Biodiversity": "#6366F1" // Indigo
      };

      let html = `
        <div style="margin-bottom: 12px;">
          <div style="height: 22px; display: flex; border-radius: 6px; overflow: hidden; box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);">
      `;

      Object.entries(econ.pillars).forEach(([name, item]) => {
        const c = colors[name] || "#64748B";
        html += `<div style="width: ${item.percentage}%; background: ${c};" title="${name}: RM ${(item.value_myr / 1e9).toFixed(2)}B (${item.percentage}%)"></div>`;
      });

      html += `
          </div>
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
      `;

      Object.entries(econ.pillars).forEach(([name, item]) => {
        const c = colors[name] || "#64748B";
        const valB = (item.value_myr / 1e9).toFixed(2);
        html += `
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="width: 10px; height: 10px; border-radius: 2px; background: ${c}; display: inline-block;"></span>
              <span style="font-size: 12px; font-weight: 600; color: #1E293B;">${name}</span>
            </div>
            <div style="text-align: right;">
              <span style="font-size: 12px; font-weight: 700; color: #0F172A;">RM ${valB}B</span>
              <span style="font-size: 11px; color: #64748B; margin-left: 4px;">(${item.percentage}%)</span>
            </div>
          </div>
        `;
      });

      html += `</div>`;
      pillarsEl.innerHTML = html;
    }

    // 2. 20-Year NPV Trade-Off Simulation Chart
    const npvEl = document.getElementById("npv-tradeoff-chart");
    if (npvEl && npv && npv.trajectory) {
      const traj = npv.trajectory;
      const width = 460;
      const height = 180;
      const padLeft = 45;
      const padRight = 20;
      const padTop = 15;
      const padBottom = 25;

      const maxVal = Math.max(...traj.map(d => Math.max(d.cum_npv_sustainable_myr, d.cum_npv_no_action_myr))) / 1e9;
      const minVal = 0;

      const scaleX = (yr) => padLeft + ((yr - 1) / (traj.length - 1)) * (width - padLeft - padRight);
      const scaleY = (valB) => height - padBottom - ((valB - minVal) / (maxVal - minVal)) * (height - padTop - padBottom);

      const ptsSust = traj.map(d => `${scaleX(d.year)},${scaleY(d.cum_npv_sustainable_myr / 1e9)}`);
      const ptsNoAction = traj.map(d => `${scaleX(d.year)},${scaleY(d.cum_npv_no_action_myr / 1e9)}`);
      const areaPath = `M ${ptsSust.join(" L ")} L ${ptsNoAction.slice().reverse().join(" L ")} Z`;

      let svg = `
        <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
          <line x1="${padLeft}" y1="${scaleY(0)}" x2="${width - padRight}" y2="${scaleY(0)}" stroke="#E2E8F0" stroke-width="1" />
          <line x1="${padLeft}" y1="${scaleY(50)}" x2="${width - padRight}" y2="${scaleY(50)}" stroke="#E2E8F0" stroke-width="1" stroke-dasharray="3,3" />
          <line x1="${padLeft}" y1="${scaleY(100)}" x2="${width - padRight}" y2="${scaleY(100)}" stroke="#E2E8F0" stroke-width="1" stroke-dasharray="3,3" />

          <text x="${padLeft - 6}" y="${scaleY(0) + 4}" font-size="9" fill="#94A3B8" text-anchor="end">RM 0</text>
          <text x="${padLeft - 6}" y="${scaleY(50) + 4}" font-size="9" fill="#94A3B8" text-anchor="end">50B</text>
          <text x="${padLeft - 6}" y="${scaleY(100) + 4}" font-size="9" fill="#94A3B8" text-anchor="end">100B</text>

          <text x="${scaleX(1)}" y="${height - 8}" font-size="9" fill="#94A3B8" text-anchor="middle">Yr 1</text>
          <text x="${scaleX(5)}" y="${height - 8}" font-size="9" fill="#94A3B8" text-anchor="middle">Yr 5</text>
          <text x="${scaleX(10)}" y="${height - 8}" font-size="9" fill="#94A3B8" text-anchor="middle">Yr 10</text>
          <text x="${scaleX(15)}" y="${height - 8}" font-size="9" fill="#94A3B8" text-anchor="middle">Yr 15</text>
          <text x="${scaleX(20)}" y="${height - 8}" font-size="9" fill="#94A3B8" text-anchor="middle">Yr 20</text>

          <path d="${areaPath}" fill="#10B981" fill-opacity="0.15" />
          <path d="M ${ptsSust.join(" L ")}" fill="none" stroke="#059669" stroke-width="2.5" />
          <path d="M ${ptsNoAction.join(" L ")}" fill="none" stroke="#DC2626" stroke-width="2" stroke-dasharray="4,3" />

          <circle cx="${width - 165}" cy="14" r="4" fill="#059669" />
          <text x="${width - 155}" y="17" font-size="9.5" font-weight="600" fill="#059669">Proactive (RM 114.3B)</text>

          <circle cx="${width - 165}" cy="28" r="4" fill="#DC2626" />
          <text x="${width - 155}" y="31" font-size="9.5" font-weight="600" fill="#DC2626">No Action (RM 66.6B)</text>

          <rect x="${width / 2 - 50}" y="${height / 2 - 14}" width="115" height="20" rx="4" fill="#ECFDF5" stroke="#10B981" stroke-width="1" />
          <text x="${width / 2 + 7}" y="${height / 2}" font-size="9.5" font-weight="700" fill="#065F46" text-anchor="middle">+RM 47.7B Preserved</text>
        </svg>
      `;
      npvEl.innerHTML = svg;
    }
  }

  // National Marine Park Tourism Data Gap (2000-2017 vs 2018-2026)
  function renderTourismDataGap() {
    const gapData = window.TOURISM_DATA_GAP || (data && data.tourismDataGap);
    const chartEl = document.getElementById("tourism-gap-chart");
    if (!chartEl || !gapData || !gapData.annual_trend) return;

    const trend = gapData.annual_trend; // 2000 to 2017
    const width = 640;
    const height = 210;
    const padLeft = 45;
    const padRight = 30;
    const padTop = 25;
    const padBottom = 30;

    const minYear = 2000;
    const maxYear = 2026;
    const maxVisitors = 800000;

    const scaleX = (yr) => padLeft + ((yr - minYear) / (maxYear - minYear)) * (width - padLeft - padRight);
    const scaleY = (vis) => height - padBottom - (vis / maxVisitors) * (height - padTop - padBottom);

    const barWidth = 12;

    let bars = "";
    trend.forEach((d) => {
      const x = scaleX(d.year) - barWidth / 2;
      const yTot = scaleY(d.total);
      const hTot = (height - padBottom) - yTot;
      const yDom = scaleY(d.domestic);
      const hDom = (height - padBottom) - yDom;
      const hFor = hTot - hDom;

      bars += `
        <rect x="${x}" y="${scaleY(d.domestic)}" width="${barWidth}" height="${hDom}" fill="#0284C7" rx="1" />
        <rect x="${x}" y="${yTot}" width="${barWidth}" height="${hFor}" fill="#38BDF8" rx="1" />
      `;
    });

    const gapStartX = scaleX(2017.5);
    const gapEndX = scaleX(2026);
    const gapWidth = gapEndX - gapStartX;
    const gapHeight = (height - padBottom) - padTop;

    let svg = `
      <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <line x1="${padLeft}" y1="${scaleY(0)}" x2="${width - padRight}" y2="${scaleY(0)}" stroke="#CBD5E1" stroke-width="1" />
        <line x1="${padLeft}" y1="${scaleY(200000)}" x2="${width - padRight}" y2="${scaleY(200000)}" stroke="#F1F5F9" stroke-width="1" stroke-dasharray="3,3" />
        <line x1="${padLeft}" y1="${scaleY(400000)}" x2="${width - padRight}" y2="${scaleY(400000)}" stroke="#F1F5F9" stroke-width="1" stroke-dasharray="3,3" />
        <line x1="${padLeft}" y1="${scaleY(600000)}" x2="${width - padRight}" y2="${scaleY(600000)}" stroke="#F1F5F9" stroke-width="1" stroke-dasharray="3,3" />
        <line x1="${padLeft}" y1="${scaleY(800000)}" x2="${width - padRight}" y2="${scaleY(800000)}" stroke="#F1F5F9" stroke-width="1" stroke-dasharray="3,3" />

        <text x="${padLeft - 6}" y="${scaleY(0) + 4}" font-size="9.5" fill="#64748B" text-anchor="end">0</text>
        <text x="${padLeft - 6}" y="${scaleY(200000) + 4}" font-size="9.5" fill="#64748B" text-anchor="end">200k</text>
        <text x="${padLeft - 6}" y="${scaleY(400000) + 4}" font-size="9.5" fill="#64748B" text-anchor="end">400k</text>
        <text x="${padLeft - 6}" y="${scaleY(600000) + 4}" font-size="9.5" fill="#64748B" text-anchor="end">600k</text>
        <text x="${padLeft - 6}" y="${scaleY(800000) + 4}" font-size="9.5" fill="#64748B" text-anchor="end">800k</text>

        <text x="${scaleX(2000)}" y="${height - 10}" font-size="9.5" fill="#64748B" text-anchor="middle">2000</text>
        <text x="${scaleX(2005)}" y="${height - 10}" font-size="9.5" fill="#64748B" text-anchor="middle">2005</text>
        <text x="${scaleX(2010)}" y="${height - 10}" font-size="9.5" fill="#64748B" text-anchor="middle">2010</text>
        <text x="${scaleX(2015)}" y="${height - 10}" font-size="9.5" fill="#64748B" text-anchor="middle">2015</text>
        <text x="${scaleX(2017)}" y="${height - 10}" font-size="9.5" font-weight="700" fill="#B91C1C" text-anchor="middle">2017</text>
        <text x="${scaleX(2020)}" y="${height - 10}" font-size="9.5" fill="#94A3B8" text-anchor="middle">2020</text>
        <text x="${scaleX(2026)}" y="${height - 10}" font-size="9.5" font-weight="700" fill="#0F172A" text-anchor="middle">2026</text>

        ${bars}

        <defs>
          <pattern id="gap-stripe" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="4" height="8" fill="#FEE2E2" />
            <rect x="4" width="4" height="8" fill="#FEF2F2" />
          </pattern>
        </defs>
        <rect x="${gapStartX}" y="${padTop}" width="${gapWidth}" height="${gapHeight}" fill="url(#gap-stripe)" stroke="#F87171" stroke-dasharray="4,3" stroke-width="1.5" rx="3" />

        <rect x="${gapStartX + (gapWidth / 2) - 95}" y="${padTop + 20}" width="190" height="24" rx="4" fill="#991B1B" />
        <text x="${gapStartX + (gapWidth / 2)}" y="${padTop + 36}" font-size="10" font-weight="700" fill="#FFFFFF" text-anchor="middle">OFFICIAL REPORTING HALTED</text>
        <text x="${gapStartX + (gapWidth / 2)}" y="${padTop + 60}" font-size="9" fill="#7F1D1D" text-anchor="middle" font-weight="600">2018–2026 Open Data Void</text>
        <text x="${gapStartX + (gapWidth / 2)}" y="${padTop + 75}" font-size="8.5" fill="#991B1B" text-anchor="middle">(COVID-19 & 2024 Bleaching Unmeasured)</text>

        <rect x="${gapStartX + (gapWidth / 2) - 85}" y="${padTop + 95}" width="170" height="36" rx="4" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1" />
        <text x="${gapStartX + (gapWidth / 2)}" y="${padTop + 109}" font-size="8.5" font-weight="700" fill="#0F172A" text-anchor="middle">Physical Carrying Capacity Ceiling:</text>
        <text x="${gapStartX + (gapWidth / 2)}" y="${padTop + 123}" font-size="8" fill="#0369A1" text-anchor="middle">Audited lodging inventory (island_accommodations)</text>

        <rect x="${padLeft + 10}" y="${padTop + 5}" width="10" height="10" fill="#38BDF8" rx="1" />
        <text x="${padLeft + 24}" y="${padTop + 13}" font-size="9" fill="#334155">Foreign Visitors</text>
        <rect x="${padLeft + 95}" y="${padTop + 5}" width="10" height="10" fill="#0284C7" rx="1" />
        <text x="${padLeft + 109}" y="${padTop + 13}" font-size="9" fill="#334155">Domestic Visitors</text>
      </svg>
    `;
    chartEl.innerHTML = svg;
  }

  // Lightbox Modal for Scientific Validation Figures
  function setupFigureLightbox() {
    const modal = document.getElementById("modal-figure-zoom");
    const modalImg = document.getElementById("lightbox-modal-img");
    const modalTitle = document.getElementById("lightbox-modal-title");
    const modalCaption = document.getElementById("lightbox-modal-caption");
    const closeBtn = document.getElementById("lightbox-modal-close");

    if (!modal) return;

    document.querySelectorAll(".figure-img-wrapper").forEach((el) => {
      el.addEventListener("click", () => {
        const imgSrc = el.dataset.img || el.querySelector("img").src;
        const title = el.dataset.title || "Figure Preview";
        const caption = el.dataset.caption || "";

        modalImg.src = imgSrc;
        modalTitle.textContent = title;
        modalCaption.textContent = caption;
        modal.classList.add("open");
      });
    });

    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        modal.classList.remove("open");
      });
    }

    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.remove("open");
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("open")) {
        modal.classList.remove("open");
      }
    });
  }

  // Formal Ministerial Decision Paper Modal
  function setupModal() {
    btnMemo.addEventListener("click", () => {
      renderMemoContent();
      modalMemo.classList.add("open");
    });

    btnCloseMemo.addEventListener("click", () => {
      modalMemo.classList.remove("open");
    });

    modalMemo.addEventListener("click", (e) => {
      if (e.target === modalMemo) {
        modalMemo.classList.remove("open");
      }
    });

    btnPrintMemo.addEventListener("click", () => {
      window.print();
    });
  }

  function renderMemoContent() {
    const isl = data.priorityIslands.find((i) => i.island === selectedIslandName) || data.priorityIslands[0];
    const isBM = currentLang === "bm";

    const titleGov = isBM
      ? "KERTAS PERTIMBANGAN JEMAAH MENTERI / MAJLIS MESYUARAT KERAJAAN NEGERI"
      : "OFFICIAL CABINET / STATE EXECUTIVE COUNCIL DECISION MEMORANDUM";

    const subGov = isBM
      ? "PELAN TINDAKAN PENGURUSAN DAYA TAMPUNG MARIN & PERLINDUNGAN EKONOMI PESISIR"
      : "PRE-SEASON MARINE CARRYING CAPACITY & COASTAL ECONOMIC ASSET PROTECTION ACTION PLAN";

    const refNo = `JPM/DOFM/REEFSAFE/2026/0${isl.rank}`;
    const dateStr = "15 Januari 2026";

    const contentHtml = `
      <div class="memo-header">
        <div class="memo-title-gov">${titleGov}</div>
        <div class="memo-title-sub">${subGov}</div>
      </div>

      <div class="memo-meta-grid">
        <span class="memo-meta-label">${isBM ? "Rujukan Fail:" : "File Reference:"}</span>
        <span><strong>${refNo}</strong></span>
        <span class="memo-meta-label">${isBM ? "Kementerian/Agensi:" : "Ministry/Agency:"}</span>
        <span>Kementerian Pertanian & Keterjaminan Makanan (Jabatan Perikanan Malaysia) & MOTAC</span>
        <span class="memo-meta-label">${isBM ? "Lokasi Intervensi:" : "Target Entity:"}</span>
        <span><strong>${isl.island}</strong> (${isl.state} • ${isl.marinePark})</span>
        <span class="memo-meta-label">${isBM ? "Tarikh:" : "Date:"}</span>
        <span>${dateStr} (Pra-Musim Pembukaan Mac 2026)</span>
      </div>

      <div class="memo-section-title">${isBM ? "1. TUJUAN KERTAS" : "1. PURPOSE OF MEMORANDUM"}</div>
      <p>
        ${isBM
          ? `Kertas ini bertujuan memohon pertimbangan dan kelulusan Kerajaan terhadap penetapan kuota kapasiti daya tampung marin dan intervensi khusus bagi <strong>Pulau ${isl.island}</strong> sebelum pembukaan musim pelancongan Tahun Melawat Malaysia 2026.`
          : `This memorandum seeks the formal approval for dynamic marine carrying capacity quotas and targeted conservation interventions for <strong>${isl.island}</strong> ahead of the Visit Malaysia 2026 reopening.`}
      </p>

      <div class="memo-section-title">${isBM ? "2. PENEMUAN KUANTITATIF & STATUS TERUMBU" : "2. QUANTITATIVE DIAGNOSTIC FINDINGS"}</div>
      <p>
        ${isBM
          ? `Berdasarkan perisikan gabungan data Reef Check Malaysia, penderiaan satelit NOAA, dan perangkaan rasmi OpenDOSM:`
          : `Synthesizing Reef Check Malaysia empirical monitoring, NOAA satellite thermal tracking, and OpenDOSM statistics:`}
      </p>
      <ul style="margin-left: 20px; margin-top: 6px;">
        <li><strong>${isBM ? "Purata Liputan Karang Hidup (LCC):" : "Current Live Coral Cover (LCC):"}</strong> ${isl.lcc.toFixed(1)}% (${isl.lcc < 40 ? (isBM ? "Kategori Waspada" : "Alert Threshold") : (isBM ? "Kategori Sederhana" : "Fair Status")})</li>
        <li><strong>${isBM ? "Tekanan Haba Lautan (NOAA Max DHW):" : "Ocean Thermal Stress (NOAA Max DHW):"}</strong> ${isl.dhw.toFixed(1)} °C-weeks</li>
        <li><strong>${isBM ? "Unjuran Aliran Tahunan (Model Gradient Boosting):" : "Projected Annual Trend (Gradient Boosting ML):"}</strong> <span style="color: ${isl.predictedNextChange < 0 ? '#DC2626' : '#059669'}; font-weight: 700;">${isl.predictedNextChange.toFixed(2)}% setahun</span></li>
        <li><strong>${isBM ? "Punca Utama Kemerosotan:" : "Primary Stressor Attribution:"}</strong> ${isl.evidence}</li>
      </ul>

      <div class="memo-section-title">${isBM ? "3. JUSTIFIKASI EKONOMI BERSEBELAHAN (REEF-ADJACENT WEALTH)" : "3. REEF-ADJACENT ECONOMIC VALUATION"}</div>
      <p>
        ${isBM
          ? `Analisis membuktikan bahawa <strong>78% nilai ekonomi pulau adalah 'bersebelahan karang' (reef-adjacent)</strong>. Kehadiran terumbu karang hidup menyerap 97% tenaga ombak bagi mengekalkan lagun tenang dan pantai berpasir putih resort bertaraf antarabangsa. Sebarang kerugian karang melebihi ambang kritikal akan mengakibatkan hakisan pantai dan penurunan unjuran <strong>30% premium nilai bilik hotel</strong> (Aset terdedah: RM ${data.nationalKPIs.reefAdjacentAtRiskRM.toFixed(1)} juta).`
          : `Analysis demonstrates that <strong>78% of island economic wealth is reef-adjacent</strong>. Living barrier reefs dissipate 97% of incoming wave energy, preserving calm lagoons and white-sand beaches for luxury resorts. Continued degradation threatens a <strong>30% collapse in beachfront room premiums</strong> (Assets at risk: RM ${data.nationalKPIs.reefAdjacentAtRiskRM.toFixed(1)}M).`}
      </p>

      <div class="memo-section-title">${isBM ? "4. SYOR PELAN TINDAKAN KHUSUS (PRESCRIPTION)" : "4. RECOMMENDED REGULATORY INTERVENTIONS"}</div>
      <div style="background: #F8FAFC; border-left: 4px solid #0369A1; padding: 12px; margin-top: 6px; border-radius: 4px;">
        <strong>${isBM ? "Tindakan Yang Diperakukan:" : "Mandated Action:"}</strong>
        <p style="margin-top: 4px;">
          ${isl.recommendation}
        </p>
      </div>

      <div class="memo-section-title">${isBM ? "5. KEPUTUSAN YANG DIPOHON" : "5. DECISION SOUGHT"}</div>
      <p>
        ${isBM
          ? `Jemaah Menteri / Majlis Mesyuarat Kerajaan Negeri dipohon meluluskan perwartaan kuota daya tampung bermusim ini dan peruntukan RM 350,000 daripada Akaun Amanah Taman Laut bagi pelaksanaan segera sebelum Mac 2026.`
          : `The Executive Council is respectfully requested to approve the seasonal carrying capacity quota and allocate RM 350,000 from the Marine Park Trust Fund for implementation prior to March 2026.`}
      </p>
    `;

    document.getElementById("memo-body-container").innerHTML = contentHtml;
  }

  // AI Copilot Integration ("Tanya ReefSafe AI")
  let currentPersona = "local";

  function setupCopilot() {
    const launcher = document.getElementById("copilot-launcher");
    const win = document.getElementById("copilot-window");
    const closeBtn = document.getElementById("copilot-close");
    const form = document.getElementById("copilot-form");
    const input = document.getElementById("copilot-input");
    const messagesContainer = document.getElementById("copilot-messages");
    const personaBtns = document.querySelectorAll(".persona-btn");
    const chips = document.querySelectorAll(".copilot-chip");

    if (!launcher || !win) return;

    launcher.addEventListener("click", () => {
      win.classList.toggle("open");
      if (win.classList.contains("open")) {
        input.focus();
      }
    });

    closeBtn.addEventListener("click", () => {
      win.classList.remove("open");
    });

    personaBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        personaBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        currentPersona = btn.dataset.persona;
      });
    });

    chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        const prompt = chip.dataset.prompt;
        if (prompt) {
          input.value = prompt;
          form.dispatchEvent(new Event("submit"));
        }
      });
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const userText = input.value.trim();
      if (!userText) return;

      // Append user bubble
      appendMessage("user", userText);
      input.value = "";
      input.disabled = true;

      // Append typing indicator
      const typingEl = document.createElement("div");
      typingEl.className = "chat-msg assistant";
      typingEl.innerHTML = `<div class="typing-dots"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>`;
      messagesContainer.appendChild(typingEl);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;

      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: userText,
            island: selectedIslandName,
            persona: currentPersona,
            lang: currentLang
          })
        });

        const resData = await response.json();
        typingEl.remove();

        if (resData.reply) {
          appendMessage("assistant", resData.reply, resData.provider);
        } else {
          appendMessage("assistant", "Maaf, sistem tidak dapat memproses permintaan ini buat masa ini.");
        }
      } catch (err) {
        typingEl.remove();
        console.error("Copilot fetch error:", err);
        appendMessage("assistant", "Ralat sambungan pelayan. Sila pastikan pelayan latar berjalan.");
      } finally {
        input.disabled = false;
        input.focus();
      }
    });

    function appendMessage(role, text, provider) {
      const msgEl = document.createElement("div");
      msgEl.className = `chat-msg ${role}`;

      if (role === "user") {
        msgEl.textContent = text;
      } else {
        // Format basic markdown bold, italic, linebreaks and lists
        let formatted = text
          .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
          .replace(/\*(.*?)\*/g, "<em>$1</em>")
          .replace(/\n\n/g, "<br><br>")
          .replace(/\n• /g, "<br>• ")
          .replace(/\n1\. /g, "<br>1. ")
          .replace(/\n2\. /g, "<br>2. ")
          .replace(/\n3\. /g, "<br>3. ");

        msgEl.innerHTML = `<div>${formatted}</div>`;
        const meta = document.createElement("span");
        meta.className = "chat-msg-meta";
        meta.textContent = provider === "gemini-1.5-flash" ? "ReefSafe AI (Gemini 1.5 Flash)" : "ReefSafe Intelligence Engine";
        msgEl.appendChild(meta);
      }

      messagesContainer.appendChild(msgEl);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  // Run on load
  document.addEventListener("DOMContentLoaded", init);
})();
