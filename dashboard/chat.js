(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.ReefSafeChat = api;
}(typeof window !== "undefined" ? window : null, function () {
  "use strict";

  const VISITOR_DESTINATIONS = new Set(["Kapalai"]);
  const SOURCE_LINKS = [
    { label: "Reef Check Malaysia annual reports", href: "https://reefcheck.org.my/annualsurveyreports/" },
    { label: "NOAA Coral Reef Watch", href: "https://coralreefwatch.noaa.gov/product/vs/data.php" },
    { label: "Sabah Parks visitor statistics", href: "https://dashboard.sabahparks.org.my" },
    { label: "2024 Malaysia coral bleaching report", href: "https://reefcheck.org.my/wp-content/uploads/2025/07/2024CoralBleachingImpactReportMalaysia.pdf" },
    { label: "Marine biodiversity economic valuation", href: "https://wdpa.s3.amazonaws.com/Country_informations/MYS/TOTAL%20ECONOMIC%20VALUE%20OF%20MARINE%20BIODIVERSITY.pdf" },
  ];
  const ECONOMY_METHOD_LINKS = [
    { label: "DOSM Domestic Tourism Survey 2024", href: "https://www.dosm.gov.my/portal-main/release-content/domestic-tourism-survey-2024" },
    { label: "Coral reef tourism method", href: "https://www.nature.org/content/dam/tnc/nature/en/documents/paper_coralreeftourism_spalding_2017.pdf" },
    { label: "Reef recovery period", href: "https://www.jcu.edu.au/news/releases/2019/february/how-long-does-it-take-coral-reefs-to-recover-from-bleaching" },
  ];

  function makeAnswer(title, sections, options) {
    return Object.assign({
      title,
      sections,
      text: [title, ...sections.map((section) => `${section.label}: ${section.text}`)].join("\n"),
      pose: "answer",
      links: [],
    }, options);
  }

  function formatChange(value) {
    return `${value >= 0 ? "+" : "−"}${Math.abs(value).toFixed(2)} pp/yr`;
  }

  function findIsland(question, islands, contextIsland) {
    const lower = question.toLowerCase();
    return islands.find((unit) => lower.includes(unit.island.toLowerCase()))
      || islands.find((unit) => unit.island === contextIsland);
  }

  function islandAnswer(unit, safetyQuestion) {
    const range = `${formatChange(unit.predictionLower)} to ${formatChange(unit.predictionUpper)}`;
    const insight = unit.stress && unit.stress.insight
      ? `${unit.stress.insight.replace(/[.!?]+$/, "")}.`
      : "Review the monitoring evidence before drawing conclusions.";
    const limit = safetyQuestion
      ? "ReefSafe does not classify destinations as safe or unsafe for visitors. This is a field-screening signal, not a closure or travel decision."
      : "This is a field-screening signal, not a precise forecast, closure, or travel-safety decision.";
    return makeAnswer(`${unit.island} overview`, [
      { label: "Status", text: `${unit.tier}; latest observed live coral cover is ${unit.lcc.toFixed(1)}% (${unit.surveyYear}).` },
      { label: "Model signal", text: `${formatChange(unit.predictedNextChange)}, with a wide uncertainty range of ${range}.` },
      { label: "What to check", text: insight },
      { label: "Important limit", text: limit },
    ], {
      pose: safetyQuestion || unit.tier === "High screening priority" ? "warn" : unit.predictedNextChange >= 0 ? "happy" : "answer",
      island: unit.island,
    });
  }

  function highestPriorityAnswer(data) {
    const highest = [...(data.priorityIslands || [])].sort((a, b) => a.rank - b.rank)[0];
    if (!highest) return makeAnswer("Highest screening priority", [{ label: "Status", text: "No monitoring-unit ranking is available." }], { pose: "warn" });
    return makeAnswer("Highest screening priority", [
      { label: "Monitoring unit", text: `${highest.island} is currently ranked 1 of ${data.priorityIslands.length}.` },
      { label: "Model signal", text: `${formatChange(highest.predictedNextChange)}, with an uncertainty range of ${formatChange(highest.predictionLower)} to ${formatChange(highest.predictionUpper)}.` },
      { label: "What it means", text: "This unit is first in ReefSafe’s queue for earlier field verification." },
      { label: "Important limit", text: "Highest screening priority does not mean highest ecological danger or visitor-safety risk." },
    ], { pose: "warn", island: highest.island });
  }

  function judgeAnswer(intent, data) {
    const answers = {
      priority_method: () => {
        const count = data.nationalKPIs.surveyedUnits;
        const high = data.nationalKPIs.priorityCount;
        return makeAnswer("Priority ranking calculation", [
          { label: "Ranking", text: "Monitoring units are sorted by predicted next annualised coral-cover change in ascending order, so the strongest predicted declines appear first." },
          { label: "Tier rule", text: `From ${count} ranked units, the first 25% become the highest-priority tier: ${high} units. All remaining units are labelled Monitor.` },
          { label: "Important limit", text: "The ranking combines a modest model signal with uncertainty; it prioritises field verification and does not measure total ecological risk or visitor safety." },
        ]);
      },
      uncertainty: () => {
        const metrics = data.modelMetrics;
        return makeAnswer("Prediction uncertainty", [
          { label: "Method", text: `The range uses the pooled empirical 95% forward-test residual distribution from ${metrics.evaluation_observations} observations.` },
          { label: "Calculation", text: `ReefSafe adds the lower residual (${formatChange(metrics.lower_residual_quantile)}) and upper residual (${formatChange(metrics.upper_residual_quantile)}) to each unit’s point prediction.` },
          { label: "Meaning", text: "The wide ranges show that the model is suitable for screening, not precise island-level forecasting." },
        ]);
      },
      problem_scope_sdg: () => makeAnswer("Problem, scope and SDG", [
        { label: "Problem", text: "Malaysia has recurring reef observations, but limited recent island-level tourism exposure data and no tool that turns uncertain model signals into a transparent field-check queue." },
        { label: "Scope", text: "ReefSafe covers the 40 monitoring units surveyed in 2025 and predicts the next observed annualised coral-cover change; it does not automate closures, quotas, or travel advice." },
        { label: "SDG relevance", text: "The main alignment is SDG 14—Life Below Water—especially evidence-led monitoring and conservation; the economic context also supports resilient coastal livelihoods." },
      ]),
      data_quality: () => makeAnswer("Data quality and integrity", [
        { label: "Official evidence", text: "The ecological model uses Reef Check Malaysia observations. NOAA, DOSM, marine-park visitor statistics, Sabah Parks, and the Department of Marine Park Malaysia provide contextual evidence." },
        { label: "Quality controls", text: "Schemas, units, years, island names, duplicates, missingness, and source provenance are checked. Missing model inputs use fold-local median imputation, fitted only on each training fold." },
        { label: "Integrity limit", text: "Unavailable island-level visitor data are left unavailable rather than fabricated, and contextual datasets are not presented as causal model inputs." },
      ], { links: SOURCE_LINKS }),
      data_integration: () => makeAnswer("Data integration", [
        { label: "Combined evidence", text: "ReefSafe joins structured ecological surveys, geospatial island coordinates, regional NOAA thermal context, official visitor series, and published economic valuation." },
        { label: "New value", text: "The integration connects reef condition, model uncertainty, field-verification priority, local stress evidence, and clearly bounded economic context in one workflow." },
        { label: "Important limit", text: "Different spatial and time resolutions are preserved; state or park totals are not downscaled into invented island estimates." },
      ]),
      dashboard_design: () => makeAnswer("Dashboard design", [
        { label: "User journey", text: "The dashboard moves from national overview to ranked field queue, then to island diagnostics and scientific evidence." },
        { label: "Usability", text: "Consistent colours, plain-language labels, uncertainty ranges, source links, responsive controls, and Reefy support the field-verification workflow." },
        { label: "Interpretation", text: "Red, orange, and green communicate screening priority—not reef safety, closures, or guaranteed future condition." },
      ]),
      implementation_impact: () => makeAnswer("Implementation and real-world impact", [
        { label: "Primary users", text: "Marine-park managers, rangers, researchers, conservation organisations, and policy teams can use ReefSafe to decide where earlier verification is most useful." },
        { label: "Operating model", text: "Refresh verified observations, rerun the reproducible pipeline, review the ranked queue, conduct field checks, and record the response before any management action." },
        { label: "Public benefit", text: "Earlier evidence gathering can improve allocation of limited monitoring resources while keeping uncertainty and non-causal limitations visible." },
      ]),
      commercial_scalability: () => makeAnswer("Commercial potential and scalability", [
        { label: "Value proposition", text: "ReefSafe is a decision-support product for monitoring prioritisation, reporting, and transparent evidence review—not a consumer safety rating." },
        { label: "Potential model", text: "A deployable version could support agency subscriptions, conservation reporting, or licensed monitoring workspaces while keeping core public evidence accessible." },
        { label: "Scale path", text: "Add verified monitoring locations through the same schema and retrain only after comparable outcome data exist; do not transfer Malaysian estimates blindly to other regions." },
      ]),
      innovation: () => makeAnswer("Creativity and innovation", [
        { label: "Combination", text: "ReefSafe combines forward-tested machine learning, geospatial exploration, prediction attribution, uncertainty, economic context, and AI-assisted question routing." },
        { label: "Original element", text: "Reefy uses Gemini to understand typos and paraphrases, but retrieves fixed, verified dashboard answers so the language model does not invent scientific claims." },
        { label: "Wow factor", text: "The interactive field queue links a national view to explainable island diagnostics and a conversational guide with an animated reef avatar." },
      ]),
      evidence_tab: () => makeAnswer("Tab 3: Evidence", [
        { label: "Coral condition and heat", text: "Shows coral-cover history and regional NOAA heat stress. The heat series is context and is not used by the production model." },
        { label: "Tourism and reef value", text: "Shows the official visitor-data gap and the separate published RM8.7 billion marine-park valuation." },
        { label: "Factors linked to coral change", text: "Shows single-factor associations and model input importance. These describe relationships and prediction—not causes." },
        { label: "Model check", text: "Shows candidate-model performance, predicted versus observed values, validation by year, and model-input coverage." },
      ]),
      model_input_coverage: () => makeAnswer("Model input coverage", [
        { label: "Meaning", text: "Coverage is the share of training cases in which each model input was actually recorded before missing values were handled." },
        { label: "Result", text: "Most inputs exceed 97% coverage; the previous coral-cover change rate is lowest at 86.1%." },
        { label: "Missing values", text: "Gaps are filled with the median inside each training fold so future test data do not influence training." },
        { label: "Important limit", text: "High completeness does not guarantee accurate measurement or causal evidence." },
      ], { links: [SOURCE_LINKS[0]] }),
      demo_promotion: () => makeAnswer("Demo promotion — Reef-Friendly Escape", [
        { label: "Demo status", text: "This is a fictional demo concept for the ReefSafe presentation—not a live commercial offer." },
        { label: "Featured destination", text: "Kapalai, the verified visitor destination currently shown with a non-negative ReefSafe screening signal." },
        { label: "Sample experience", text: "A low-impact island visit with a reef etiquette briefing, reusable visitor kit, and a guided introduction to reef monitoring." },
        { label: "Availability", text: "Demo only and not bookable. Confirm real prices, operators, permits, weather, and travel advice with official providers." },
      ], { pose: "happy" }),
    };
    return answers[intent] ? answers[intent]() : null;
  }

  function answerQuestion(question, data, contextIsland) {
    const clean = String(question || "").trim();
    const lower = clean.toLowerCase();
    const islands = data.priorityIslands || [];
    const mentionedUnit = islands.find((item) => lower.includes(item.island.toLowerCase()));
    const usesContext = /\b(this|current|selected)\s+(reef|island|unit)\b|\bhow is (it|this)\b/.test(lower);
    const unit = mentionedUnit || (usesContext ? islands.find((item) => item.island === contextIsland) : undefined);

    if (/demo promotion|mock promotion|sample package/.test(lower)) {
      return judgeAnswer("demo_promotion", data);
    }

    if (/promotion|package|deal|discount|book|booking|weather|travel advisory|medical|diving safety/.test(lower)) {
      return makeAnswer("Live travel information unavailable", [
        { label: "Not available", text: "ReefSafe has no verified live promotion data, booking availability, weather, medical advice, or official travel advisories." },
        { label: "Next step", text: "Please check official sources and marine park authorities before making travel decisions." },
      ], { pose: "warn" });
    }

    if (/safe|unsafe|should i (go|visit)|can i (go|visit)/.test(lower)) {
      const safetyUnit = mentionedUnit || islands.find((item) => item.island === contextIsland);
      return safetyUnit
        ? islandAnswer(safetyUnit, true)
        : makeAnswer("Travel-safety limitation", [
          { label: "Important limit", text: "ReefSafe does not classify destinations as safe or unsafe." },
          { label: "Try asking", text: "Name a monitored island and I can explain its field-screening evidence." },
        ], { pose: "warn" });
    }

    if (/compare|versus|\bvs\b/.test(lower)) {
      const compared = islands.filter((item) => lower.includes(item.island.toLowerCase())).slice(0, 2);
      if (compared.length === 2) {
        return makeAnswer("Monitoring-unit comparison", [
          { label: compared[0].island, text: `${compared[0].tier}; ${formatChange(compared[0].predictedNextChange)}.` },
          { label: compared[1].island, text: `${compared[1].tier}; ${formatChange(compared[1].predictedNextChange)}.` },
          { label: "Important limit", text: "These are field-screening results, not a safety rating." },
        ]);
      }
    }

    if (/alternative|greener|green (island|destination|reef)|(where|which|what).*visit|good.*visit/.test(lower)) {
      const choices = islands.filter((item) => VISITOR_DESTINATIONS.has(item.island)
        && item.tier !== "High screening priority" && item.predictedNextChange >= 0);
      if (!choices.length) return makeAnswer("No greener alternative found", [
        { label: "Result", text: "No verified visitor destination currently meets the dashboard's green-screening rule." },
      ], { pose: "warn" });
      const best = choices.sort((a, b) => b.predictedNextChange - a.predictedNextChange)[0];
      return makeAnswer("Greener monitored alternative", [
        { label: "Suggestion", text: `${best.island} is a verified visitor destination represented in ReefSafe.` },
        { label: "Dashboard signal", text: `Its predicted change is non-negative at ${formatChange(best.predictedNextChange)}.` },
        { label: "Important limit", text: "This is not a safety rating; check official travel information before visiting." },
      ], {
        pose: "happy",
        island: best.island,
      });
    }

    if (/highest.*(risk|priority)|most (urgent|at risk)|worst.*(prediction|decline)/.test(lower)) {
      return highestPriorityAnswer(data);
    }

    if (/priority.*(tier|rank|calculat|method)|how.*(rank|tier)/.test(lower)) return judgeAnswer("priority_method", data);
    if (/uncertain|prediction.*(range|interval)|confidence.*(range|interval)/.test(lower)) return judgeAnswer("uncertainty", data);

    if (/season.*rest|rest.*season|long.term.*reef.*(revenue|value)|short.term.*long.term/.test(lower)) {
      const tradeoff = data.tourismEconomics.tradeoff;
      return makeAnswer("Season rest calculation", [
        { label: "One-month proxy", text: `The four covered parks have RM${(tradeoff.short_term_loss_rm * 12 / 1e6).toFixed(2)}M annual spending. Dividing by 12 gives RM${(tradeoff.short_term_loss_rm / 1e6).toFixed(2)}M for one month.` },
        { label: "Annual reef-adjacent value", text: `Applying the stated 10% reef-attributable share gives RM${(tradeoff.reef_adjacent_annual_rm / 1e6).toFixed(2)}M a year.` },
        { label: "Long-term arithmetic", text: `Over 10 years that is RM${(tradeoff.long_term_low_rm / 1e6).toFixed(2)}M; over 15 years it is RM${(tradeoff.long_term_high_rm / 1e6).toFixed(2)}M, undiscounted.` },
        { label: "Important limit", text: "The 12–18× ratio is fixed by the assumptions. It is not a forecast of revenue, avoided loss, or coral recovery caused by a rest period." },
      ], { links: ECONOMY_METHOD_LINKS });
    }

    if (/reef[- ]adjacent economy(?! potential)/.test(lower)) {
      const economics = data.tourismEconomics;
      return makeAnswer("Reef-adjacent economy calculation", [
        { label: "Concept", text: "It measures the portion of coastal tourism and economic value directly linked to healthy coral reefs, reflecting their contribution to local livelihoods." },
        { label: "Formula", text: "For each covered marine park: annual visitors × RM410 average spending per visitor × 10% reef-attributable share." },
        { label: "National estimate", text: `The covered parks represent ${(economics.national_visitors).toLocaleString("en-MY")} visitors and RM${(economics.national_spending_rm / 1e6).toFixed(2)}M spending; 10% gives RM${(economics.national_reef_adjacent_rm / 1e6).toFixed(2)}M a year.` },
        { label: "Coverage", text: `${economics.units_covered} of ${economics.units_total} monitoring units are inside parks with published visitor counts. Uncovered units are excluded rather than estimated.` },
        { label: "Important limit", text: "This is a spending proxy using a global 10% coefficient—not current island revenue, an asset value, or a forecast." },
      ], { links: ECONOMY_METHOD_LINKS.slice(0, 2) });
    }

    if (/(mean|average).*coral.*cover|coral.*cover.*(mean|average)|39\.8%|40 units surveyed/.test(lower)) {
      const kpi = data.nationalKPIs;
      return makeAnswer("Mean coral cover calculation", [
        { label: "Coverage", text: `For all ${kpi.surveyedUnits} ranked monitoring units surveyed in 2025, ReefSafe takes the latest live-coral-cover observation and calculates an arithmetic mean.` },
        { label: "Calculation", text: `Their percentages are added and divided by ${kpi.surveyedUnits}. The arithmetic mean is ${kpi.latestMeanCoralCover.toFixed(4)}%, displayed as ${kpi.latestMeanCoralCover.toFixed(1)}%.` },
        { label: "Important limit", text: "Each monitoring unit has equal weight; the result does not weight units by reef area, number of sites, or visitor volume." },
      ], { links: [SOURCE_LINKS[0]] });
    }

    if (/\b(recent|current|latest)?\s*coverage\b/.test(lower)) {
      return makeAnswer("Which coverage do you mean?", [
        { label: "Coral condition", text: "Ask “How is mean coral cover calculated?” for the 39.8% KPI." },
        { label: "Model completeness", text: "Ask “What is model input coverage?” for the Evidence-tab completeness chart." },
        { label: "Economy coverage", text: "Ask “Which units are covered by the reef-adjacent economy estimate?” for the 30-of-40 figure." },
      ], { pose: "wave" });
    }

    if (/stress.*(factor|contribution)|factor.*contribution|contribution.*calculat/.test(lower)) {
      return makeAnswer("Stress-factor contribution", [
        { label: "Method", text: "For each monitoring unit, ReefSafe traces its path through every tree in the Gradient Boosting model and credits each split’s change in node value to the feature used at that split." },
        { label: "Grouping", text: "Feature credits are summed into eight factor groups. The model baseline plus all factor groups equals the published prediction exactly, in percentage points per year." },
        { label: "Display rule", text: "A measured stressor is named only when its contribution pushes the prediction toward decline by at least 0.25 pp/yr." },
        { label: "Important limit", text: "This explains the model’s prediction; it is not a causal estimate of environmental damage." },
      ]);
    }

    if (/actionable.*insight|insight.*(come|derive|calculat|select)|why.*(recommend|action)/.test(lower)) {
      return makeAnswer("Actionable insight", [
        { label: "Selection", text: "ReefSafe selects the most negative measured stressor group contributing at least 0.25 pp/yr toward decline." },
        { label: "Translation", text: "That group maps to a conservative field check—for example, pollution and waste maps to inspecting wastewater and waste controls." },
        { label: "Below threshold", text: "If no measured stressor crosses the threshold, ReefSafe recommends field verification instead of naming a driver." },
        { label: "Important limit", text: "The insight is a screening prompt, not proof of cause and not an automatic decision." },
      ]);
    }

    if (/reef[- ]adjacent economy potential|economy potential/.test(lower)) {
      return makeAnswer("Reef-Adjacent Economy Potential source", [
        { label: "Source", text: "Department of Marine Park Malaysia, Total Economic Value of Marine Biodiversity: Malaysia Marine Parks." },
        { label: "Coverage", text: "Studies from 2011–2015 covering six evaluated marine-park archipelagos: Payar, Perhentian, Redang, Tioman, Tinggi, and Labuan." },
        { label: "Published value", text: "The seven components total RM8.68699 billion, reported as RM8.7 billion per year." },
        { label: "Important limit", text: "This is a historical published valuation—largely willingness-to-pay—not current revenue, visitor spending, or an island-level estimate." },
      ], { links: [SOURCE_LINKS[4]] });
    }

    if (/\b(link|links|source|sources|provenance|dataset|datasets)\b/.test(lower)) {
      return makeAnswer("Dataset sources", [
        { label: "Model evidence", text: "Reef Check Malaysia annual surveys provide the ecological observations used by the production model." },
        { label: "Context only", text: "NOAA heat, tourism, bleaching, and economic sources support context and are not production-model features." },
        { label: "Important limit", text: "State visitor totals cannot be allocated to individual reefs, and associations are not causal effects." },
      ], { links: SOURCE_LINKS });
    }

    if (/gradient|model|accur|performance|baseline/.test(lower)) {
      const metrics = data.modelMetrics;
      return makeAnswer("Why Gradient Boosting?", [
        { label: "Result", text: `${metrics.best_candidate} had the lowest forward-test MAE: ${metrics.best_mae.toFixed(3)} pp/yr.` },
        { label: "Comparison", text: `The mean baseline scored ${metrics.baseline_mae.toFixed(3)} pp/yr, so the improvement is only ${metrics.mae_improvement_pct.toFixed(1)}%.` },
        { label: "Meaning", text: "It was the best tested candidate, but the predictive signal remains weak." },
        { label: "Important limit", text: "ReefSafe uses it for screening, not precise forecasting." },
      ]);
    }

    if (/methodolog|approach|validat|train|feature|input|how.*(built|trained)/.test(lower)) {
      const metrics = data.modelMetrics;
      return makeAnswer("Methodology", [
        { label: "Approach", text: "The model predicts the next observed annualised coral-cover change from coral condition, substrate, fish and ecology, reported impacts, and geography." },
        { label: "Validation", text: `Past-only expanding-window evaluation covers ${metrics.test_years.join(", ")}, using ${metrics.training_transitions} training transitions and ${metrics.evaluation_observations} forward-test observations.` },
        { label: "Important limit", text: "NOAA heat is contextual rather than a model input, and results are screening signals—not causal findings or precise forecasts." },
      ]);
    }

    if (unit && /(how|doing|about|status|reef|island|coral|predict|change|this)/.test(lower)) {
      return islandAnswer(unit, false);
    }

    if (/summar|dashboard|colour|color|red|orange|amber/.test(lower)) {
      return makeAnswer("ReefSafe dashboard", [
        { label: "Purpose", text: "ReefSafe ranks monitored reefs for earlier field checks." },
        { label: "Colours", text: "Red means High Screening Priority; orange means Monitor with predicted decline; green means Monitor with non-negative predicted change." },
        { label: "Important limit", text: "The colours are screening signals, not safety ratings or closure decisions." },
      ]);
    }

    if (/data|limit|cause|causal|economic|value|tourism/.test(lower)) {
      return makeAnswer("Data and limitations", [
        { label: "Model evidence", text: "ReefSafe uses Reef Check Malaysia observations for the production model." },
        { label: "Context", text: "NOAA thermal stress and tourism or economic data are descriptive context." },
        { label: "Important limit", text: "The evidence cannot establish causation, prescribe closures, or provide current island-level visitor demand and revenue." },
      ]);
    }

    return makeAnswer("I need a little more detail", [
      { label: "I can help with", text: "Island screening status, greener monitored alternatives, dashboard colours, model performance, validation, data sources, economics, and ReefSafe's limitations." },
      { label: "Example", text: "Try: ‘Which island has the highest priority?’ or ‘Explain the methodology.’" },
    ], { pose: "wave" });
  }

  function answerFromIntent(classification, question, data, contextIsland) {
    if (!classification || classification.confidence < 0.6) return answerQuestion(question, data, contextIsland);
    const islands = (classification.islands || []).map((name) => {
      const match = data.priorityIslands.find((unit) => unit.island.toLowerCase() === String(name).toLowerCase());
      return match && match.island;
    }).filter(Boolean);
    const first = islands[0] || contextIsland;
    const canonical = {
      island_status: first ? `How is ${first} doing?` : question,
      compare_islands: islands.length === 2 ? `Compare ${islands[0]} and ${islands[1]}` : question,
      greener_alternative: "Suggest a greener alternative",
      dashboard_summary: "Summarise the dashboard",
      model_selection: "Why Gradient Boosting?",
      methodology: "What is the methodology?",
      validation: "How was the model validated?",
      model_features: "What model features are used?",
      dataset_sources: "Give me the dataset links",
      economy_potential_source: "Where is the Reef-Adjacent Economy Potential data from?",
      reef_economy_calculation: "How is reef-adjacent economy calculated?",
      season_rest_calculation: "How are the season rest and long term reef revenue calculated?",
      coral_cover_calculation: "How is mean coral cover 2025 39.8% for 40 units calculated?",
      stress_contribution: "How is the stress factor contribution calculated?",
      actionable_insight: "Where does the actionable insight come from?",
      demo_promotion: "Show me a demo promotion",
      limitations: "What are ReefSafe's limitations?",
      external_live_info: "live weather booking promotion travel advisory medical diving safety",
    }[classification.intent];
    if (classification.intent === "highest_priority") return highestPriorityAnswer(data);
    const judged = judgeAnswer(classification.intent, data);
    if (judged) return judged;
    return answerQuestion(canonical || question, data, first);
  }

  async function callChatApi(question, contextIsland, contextTab, history) {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, contextIsland, contextTab, history }),
    });
    if (!response.ok) throw new Error("Chat API unavailable");
    return response.json();
  }

  async function classifyWithServer(question, contextIsland, contextTab) {
    const response = await fetch("/api/chat/intent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, contextIsland, contextTab }),
    });
    if (!response.ok) throw new Error("Intent classifier unavailable");
    return response.json();
  }

  async function resolveQuestion(question, data, contextIsland, chatOrClassifier, contextTab, history) {
    try {
      const res = await (chatOrClassifier || callChatApi)(question, contextIsland, contextTab, history);
      if (res && res.sections && res.sections.length) {
        const island = res.suggestedIsland && String(res.suggestedIsland).toLowerCase() !== "none" ? res.suggestedIsland : null;
        const tab = res.suggestedTab && String(res.suggestedTab).toLowerCase() !== "none" ? res.suggestedTab : null;
        return {
          title: res.title || null,
          text: (res.sections || []).map((s) => `${s.label}: ${s.text}`).join("\n"),
          sections: res.sections,
          links: res.links || [],
          pose: res.pose || "answer",
          island: island,
          tab: tab,
        };
      }
      if (res && res.answer) {
        const island = res.suggestedIsland && String(res.suggestedIsland).toLowerCase() !== "none" ? res.suggestedIsland : null;
        const tab = res.suggestedTab && String(res.suggestedTab).toLowerCase() !== "none" ? res.suggestedTab : null;
        return {
          title: null,
          text: res.answer,
          sections: [{ text: res.answer }],
          links: res.links || [],
          pose: res.pose || "answer",
          island: island,
          tab: tab,
        };
      }
      if (res && res.intent) {
        return answerFromIntent(res, question, data, contextIsland);
      }
      return answerQuestion(question, data, contextIsland);
    } catch (_error) {
      return answerQuestion(question, data, contextIsland);
    }
  }

  function initChat(data, doc) {
    doc = doc || (typeof document !== "undefined" ? document : null);
    if (!doc || !data) return;

    const launcher = doc.getElementById("reef-chat-launcher");
    const panel = doc.getElementById("reef-chat-panel");
    const closeButton = doc.getElementById("reef-chat-close");
    const form = doc.getElementById("reef-chat-form");
    const input = doc.getElementById("reef-chat-input");
    const send = doc.getElementById("reef-chat-send");
    const messages = doc.getElementById("reef-chat-messages");
    const avatar = doc.getElementById("reef-chat-avatar");
    const launcherAvatar = launcher && launcher.querySelector("img");
    const status = doc.getElementById("reef-chat-status");
    const islandSelect = doc.getElementById("island-select");
    if (!launcher || !panel || !form || !input || !messages || !avatar) return;

    const poses = {
      idle: "waiting",
      wave: "waving",
      think: "thinking",
      answer: "answering",
      happy: "celebrating",
      warn: "showing caution",
    };
    let greeted = false;

    function setPose(pose) {
      const selected = poses[pose] ? pose : "answer";
      avatar.src = `assets/avatar/avatar_${selected}.png`;
      avatar.alt = `Reefy the diver ${poses[selected]}`;
      if (launcherAvatar) launcherAvatar.src = avatar.src;
      if (status) status.textContent = selected === "think" ? "Checking dashboard evidence…" : "ReefSafe dashboard guide";
    }

    function showDiagnostics(island) {
      if (!islandSelect) return;
      const option = Array.from(islandSelect.options).find((opt) => opt.value.toLowerCase() === island.toLowerCase());
      if (option) {
        islandSelect.value = option.value;
      } else {
        islandSelect.value = island;
      }
      islandSelect.dispatchEvent(new doc.defaultView.Event("change", { bubbles: true }));
      const tab = doc.querySelector('[data-tab="diagnostics"]');
      if (tab) tab.click();
      closeChat();
    }

    function appendMessage(text, sender, island) {
      const message = doc.createElement("div");
      message.className = `chat-msg ${sender}`;
      message.textContent = text;
      if (sender === "assistant" && island) {
        const action = doc.createElement("button");
        action.type = "button";
        action.className = "chat-action";
        action.textContent = `Show ${island} diagnostics`;
        action.addEventListener("click", () => showDiagnostics(island));
        message.appendChild(action);
      }
      messages.appendChild(message);
      messages.scrollTop = messages.scrollHeight;
    }

    function appendAnswer(answer) {
      const message = doc.createElement("div");
      message.className = "chat-msg assistant chat-card";
      if (answer.title) {
        const title = doc.createElement("strong");
        title.className = "chat-card-title";
        title.textContent = answer.title;
        message.appendChild(title);
      }
      (answer.sections || [{ text: answer.text }]).forEach((section) => {
        const row = doc.createElement("div");
        row.className = "chat-card-section";
        if (section.label) {
          const label = doc.createElement("strong");
          label.textContent = section.label;
          row.appendChild(label);
        }
        const text = section.text || "";
        if (/\b1[\.\)]\s+[\s\S]*\b2[\.\)]\s+/.test(text)) {
          const items = text.split(/\n+|(?<=[,\.;]?\s+)(?=\d+[\.\)]\s+)/)
            .map((s) => s.trim().replace(/^,\s*|\s*,\s*$/, ""))
            .filter(Boolean);
          if (items.length > 1) {
            const list = doc.createElement("ol");
            list.className = "chat-card-list";
            items.forEach((item) => {
              const cleanItem = item.replace(/^\d+[\.\)]\s*/, "").replace(/[,\.;]+$/, "");
              const li = doc.createElement("li");
              li.textContent = cleanItem;
              list.appendChild(li);
            });
            row.appendChild(list);
            message.appendChild(row);
            return;
          }
        }
        let bulletLines = [];
        if (text.includes("•")) {
          bulletLines = text.split("•").map((s) => s.trim()).filter(Boolean);
        } else if (text.includes("\n")) {
          bulletLines = text.split(/\n+/).map((s) => s.trim().replace(/^[\-\*]\s*/, "")).filter(Boolean);
        } else if (/\.\s{2,}/.test(text)) {
          bulletLines = text.split(/(?<=\.)\s{2,}/).map((s) => s.trim()).filter(Boolean);
        }
        if (bulletLines.length > 1) {
          const list = doc.createElement("ul");
          list.className = "chat-card-list";
          bulletLines.forEach((item) => {
            const cleanItem = item.replace(/^[\-\*•]\s*/, "").trim();
            if (cleanItem) {
              const li = doc.createElement("li");
              li.textContent = cleanItem;
              list.appendChild(li);
            }
          });
          row.appendChild(list);
          message.appendChild(row);
          return;
        }
        const body = doc.createElement("span");
        body.textContent = text;
        row.appendChild(body);
        message.appendChild(row);
      });
      if (answer.links && answer.links.length) {
        const links = doc.createElement("div");
        links.className = "chat-source-links";
        answer.links.forEach((source) => {
          const link = doc.createElement("a");
          link.href = source.href;
          link.target = "_blank";
          link.rel = "noopener";
          link.textContent = source.label;
          links.appendChild(link);
        });
        message.appendChild(links);
      }
      if (answer.island) {
        const action = doc.createElement("button");
        action.type = "button";
        action.className = "chat-action";
        action.textContent = `Show ${answer.island} diagnostics`;
        action.addEventListener("click", () => showDiagnostics(answer.island));
        message.appendChild(action);
      }
      if (answer.tab) {
        const action = doc.createElement("button");
        action.type = "button";
        action.className = "chat-action";
        const tabNames = { overview: "Overview", diagnostics: "Diagnostics", evidence: "Evidence", science: "Evidence" };
        action.textContent = `Open ${tabNames[answer.tab] || answer.tab} tab`;
        action.addEventListener("click", () => {
          const tabBtn = doc.querySelector(`[data-tab="${answer.tab}"]`);
          if (tabBtn) tabBtn.click();
          closeChat();
        });
        message.appendChild(action);
      }
      messages.appendChild(message);
      messages.scrollTop = messages.scrollHeight;
    }

    function openChat() {
      panel.classList.add("open");
      launcher.setAttribute("aria-expanded", "true");
      setPose("wave");
      if (!greeted) {
        appendMessage("Hi, I’m Reefy. Ask me about a monitored reef, this dashboard, or how the model was validated.", "assistant");
        greeted = true;
      }
      input.focus();
    }

    function closeChat() {
      panel.classList.remove("open");
      launcher.setAttribute("aria-expanded", "false");
      setPose("idle");
      launcher.focus();
    }

    let conversationHistory = [];

    function submitQuestion(question) {
      const clean = String(question || "").trim();
      if (!clean || send.disabled) return;
      appendMessage(clean, "user");
      input.value = "";
      input.disabled = true;
      send.disabled = true;
      setPose("think");
      setTimeout(async () => {
        const activeTab = doc.querySelector(".nav-tab.active");
        const currentTab = activeTab && activeTab.dataset.tab;
        const answer = await resolveQuestion(
          clean,
          data,
          islandSelect && islandSelect.value,
          null,
          currentTab,
          conversationHistory
        );
        appendAnswer(answer);
        setPose(answer.pose);
        conversationHistory.push({ role: "user", text: clean });
        const assistantSummary = answer.title
          ? `${answer.title}: ` + (answer.sections || []).map((s) => `${s.label} - ${s.text}`).join(". ")
          : answer.text;
        conversationHistory.push({ role: "assistant", text: assistantSummary });
        if (conversationHistory.length > 8) {
          conversationHistory = conversationHistory.slice(-8);
        }
        input.disabled = false;
        send.disabled = false;
        input.focus();
      }, 250);
    }

    launcher.addEventListener("click", () => panel.classList.contains("open") ? closeChat() : openChat());
    closeButton.addEventListener("click", closeChat);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      submitQuestion(input.value);
    });
    doc.querySelectorAll("[data-question]").forEach((button) => {
      button.addEventListener("click", () => submitQuestion(button.dataset.question));
    });
    doc.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && panel.classList.contains("open")) closeChat();
    });
  }

  return { answerQuestion, answerFromIntent, resolveQuestion, findIsland, formatChange, initChat };
}));

if (typeof window !== "undefined" && window.ReefSafeChat) {
  window.ReefSafeChat.initChat(window.REEFSAFE_DATA);
}
