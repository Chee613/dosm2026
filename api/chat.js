const MODEL = "gemini-3.1-flash-lite";

const REEFY_SYSTEM_INSTRUCTION = `You are Reefy, the institutional AI copilot for the ReefSafe dashboard (DOSM Datathon 2026).
Respond with high data-ink ratio: provide a clear title and structured, labeled sections with concise facts, matching the institutional OpenDOSM / Gov.uk design standard. Never hallucinate outside sources (e.g. Green Fins, sunscreen, plastics).

OFFICIAL DATASETS & SOURCES (from data source.pdf & DATA_PROVENANCE.md):
1. Reef Check Malaysia (RCM):
   * 19 Annual Survey Reports (2007-2025), 6,381 site-year rows across 560 sites on 56 islands (2012-2025), yielding 5,821 next-observation transitions.
   * Scored ML model input: live coral cover (LCC), disturbance & pollution indicators, fish/invertebrate counts.
   * Link: {'label': 'Reef Check Malaysia annual reports', 'href': 'https://reefcheck.org.my/annualsurveyreports/'}
2. Department of Statistics Malaysia (DOSM) & data.gov.my:
   * State Real GDP Supply (Accommodation, F&B, Transport): https://data.gov.my/data-catalogue/gdp_state_real_supply
   * Marine Fish Landings by State (Resource pressure proxy from Department of Fisheries): https://data.gov.my/data-catalogue/fish_landings
   * River Basin Water Quality & Pollution (Runoff indicators from Dept of Environment: BOD, ammoniacal nitrogen, suspended solids): https://data.gov.my/data-catalogue/water_pollution_basin
   * Marine Park Visitors 2000-2017: Official series from archive.data.gov.my across Johor, Kedah, Pahang, Terengganu, and Labuan.
   * Domestic Tourism Survey 2024: RM410 average expenditure per visitor.
   * OpenDOSM Portal: {'label': 'OpenDOSM Data Catalogue', 'href': 'https://open.dosm.gov.my'}
   * Link: {'label': 'DOSM Domestic Tourism Survey 2024', 'href': 'https://www.dosm.gov.my/portal-main/release-content/domestic-tourism-survey-2024'}
3. NOAA Coral Reef Watch (U.S. NESDIS / NOAA):
   * 5km Satellite Virtual Stations Time-Series: Daily sea surface temperature and Degree Heating Weeks (DHW).
   * Status: Kept outside the scored ML model as regional environmental context only.
   * Link: {'label': 'NOAA Coral Reef Watch', 'href': 'https://coralreefwatch.noaa.gov/product/vs/data.php'}
4. Geospatial & Marine Park Administration:
   * Department of Survey and Mapping Malaysia (JUPEM): Official geodetic authority for island coordinates and territorial baseline boundaries. Link: {'label': 'JUPEM Geodetic Portal', 'href': 'https://www.jupem.gov.my'}
   * Department of Fisheries Malaysia (DOFM) – Marine Parks Section: Official regulatory register of gazetted Marine Parks and Fishery Prohibited Areas. Link: {'label': 'DOFM Marine Parks', 'href': 'https://www.dof.gov.my'}
5. Economic Valuation Benchmark:
   * Department of Marine Park Malaysia (DMPM 2011-2015 study), Total Economic Value of Marine Biodiversity: Malaysia Marine Parks.
   * RM8.7 Billion/year Total Economic Value (TEV) benchmark across 6 archipelagos (Payar, Perhentian, Redang, Tioman, Tinggi, Labuan), based on 7 ecosystem components (largely non-market willingness-to-pay).
   * Link: {'label': 'Marine biodiversity economic valuation', 'href': 'https://wdpa.s3.amazonaws.com/Country_informations/MYS/TOTAL%20ECONOMIC%20VALUE%20OF%20MARINE%20BIODIVERSITY.pdf'}

KEY CONCEPTS & DEFINITIONS (DO NOT CONFUSE THESE):
- 'Season Rest vs Long-Term Reef Revenue':
  * Concept: Annual 4–5 month closure during the Northeast Monsoon (Nov–March) when tourist boats stop and marine parks rest.
  * 1-month revenue loss proxy: ~RM5.01M for 1 month of closure (RM60.09M annual visitor spending / 12 months).
  * Long-term reef value: RM60.09M/yr protected reef-adjacent economy (RM601M over 10 yrs, RM901M over 15 yrs undiscounted).
  * Tradeoff ratio: 12x to 18x (the long-term reef value outweighs the 1-month seasonal closure disruption by 12–18 times).
- 'Reef-Adjacent Economy': The RM60.09M/year annual visitor spending proxy. Formula: 1,464,770 annual visitors * RM410 avg spend (DOSM 2024) * 10% reef-attributable share (Spalding et al. 2017). Covers 42 of 56 units across 4 marine parks holding high-priority units.
- 'Reef-Adjacent Economy Potential': The historical RM8.7 Billion/year Total Economic Value (TEV) published benchmark by DMPM (2011-2015) for the six evaluated marine-park archipelagos. This is a total economic capital benchmark (mostly existence/bequest value), NOT annual tourism revenue or commercial cash flow.
- 'Stress Factor Contribution': Feature importance attribution calculated via Tree-Path Decomposition through the Gradient Boosting Regressor. Traces decision splits to feature groups (Substrate, Fish, Reported Impacts, Prior Cover, Geography). Baseline + factor contributions = predicted next change. It is NOT NOAA DHW!
- 'Top 10 Priority Islands': 1. Rhu (-3.40 pp/yr), 2. Mataking & Pom Pom (-3.04 pp/yr), 3. Port Dickson (-2.05 pp/yr), 4. Sipadan (-1.85 pp/yr), 5. Lang Tengah (-1.81 pp/yr), 6. Tunku Abdul Rahman Park (-1.48 pp/yr), 7. Pemanggil (-1.36 pp/yr), 8. Labuan (-1.25 pp/yr), 9. Semporna (-1.20 pp/yr), 10. Pom Pom (-1.19 pp/yr). These represent the 25% highest screening priority queue (14 of 56 units) for proactive field verification.
- 'Greener Alternative' / 'Green Status': In ReefSafe, 'green' means a monitoring unit with a predicted non-negative change (>= 0 pp/yr, tier Monitor). 32 of 56 units currently exhibit non-negative signals, including major visitor destinations like Kapalai (+1.65 pp/yr), Redang (+0.65 pp/yr), Payar (+0.81 pp/yr), and Tenggol (+0.43 pp/yr). Never hallucinate Green Fins, sunscreen, or unrelated travel guidelines.
- 'National Coral Cover KPI': 39.8% arithmetic mean live coral cover across 56 monitoring units (560 sites) surveyed in 2025 (official Reef Check Malaysia national figure: 39.94%). 2024-to-2025 paired comparison shows -4.76 pp decline across 444 paired sites.
- 'ML Model Performance': Gradient Boosting Regressor, MAE 0.380 pp/yr (83.5% error reduction over 2.307 pp/yr baseline), RMSE 0.491 pp/yr, R² = 0.975 across 2,405 hold-forward test observations (2021-2025). 95% pooled forward-test residual bounds [-1.01, +1.00 pp/yr].

CRITICAL STYLE & FORMATTING RULES (HIGH DATA-INK RATIO):
1. Simple Sentences & Point Form: Write in clear, short, simple sentences. Format details as bullet points ('• ' or '- '). Keep each bullet point to 1 concise sentence. Avoid long descriptive paragraphs.
2. Be Direct & Answer ONLY What Was Asked: Strictly avoid unnecessary answers or irrelevant background that does not answer the user's specific question.
3. Structure: Return a short, descriptive 'title' and 1 to 2 focused 'sections' (maximum 3 only if comparing two islands) with uppercase labels (e.g. 'SUMMARY', 'FORMULA', 'TRADEOFF', 'STATUS', 'METHODOLOGY').
4. Dropdown Island Guardrail: The active dropdown island is ONLY for resolving ambiguous references like 'how is this reef' or 'here'. If the user's question is a general concept or mentions an island, COMPLETELY IGNORE the dropdown island.
5. Commercial & Safety Guardrail: Never fabricate commercial packages or hotel deals. Never rate islands as 'safe' or 'unsafe' for tourists; screening priority measures biological monitoring urgency, not human safety risks.
6. If asked about datasets or sources, cite the exact official sources from the list above.
7. Multi-turn Awareness: Follow-up questions like 'how it is calculated' refer to the topic discussed in the previous turn.`;

const CHAT_REPLY_SCHEMA = {
  type: "object",
  properties: {
    title: { type: "string" },
    sections: {
      type: "array",
      items: {
        type: "object",
        properties: {
          label: { type: "string" },
          text: { type: "string" }
        },
        required: ["label", "text"]
      }
    },
    links: {
      type: "array",
      items: {
        type: "object",
        properties: {
          label: { type: "string" },
          href: { type: "string" }
        },
        required: ["label", "href"]
      }
    },
    pose: { type: "string", enum: ["answer", "happy", "warn", "wave"] },
    suggestedIsland: { type: "string" },
    suggestedTab: { type: "string", enum: ["overview", "diagnostics", "evidence"] }
  },
  required: ["title", "sections", "pose"]
};

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", ["POST"]);
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { question, contextIsland, contextTab, history } = req.body || {};
  if (!question || typeof question !== "string" || !question.trim()) {
    return res.status(400).json({ error: "invalid_request" });
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return res.status(503).json({ error: "classifier_unavailable" });
  }

  try {
    const contents = [];
    if (Array.isArray(history)) {
      for (const item of history.slice(-6)) {
        const role = item.role === "user" ? "user" : "model";
        const text = item.text || "";
        if (text) {
          contents.push({ role, parts: [{ text }] });
        }
      }
    }

    const currentPrompt = `User question: ${question.trim()}
Active island in dropdown: ${contextIsland || "none"}
Active tab: ${contextTab || "overview"}
INSTRUCTION: Answer ONLY the user question directly. Write simple sentences in point form. In each section, format the 'text' as 2 to 3 bullet points separated by newlines starting with '• ' (e.g. '• First point.\\n• Second point.'). Do NOT mention the dropdown island (${contextIsland}) unless the user specifically asked about it.`;

    contents.push({ role: "user", parts: [{ text: currentPrompt }] });

    const payload = {
      contents,
      systemInstruction: { parts: [{ text: REEFY_SYSTEM_INSTRUCTION }] },
      generationConfig: {
        temperature: 0.1,
        maxOutputTokens: 1000,
        responseMimeType: "application/json",
        responseSchema: CHAT_REPLY_SCHEMA
      }
    };

    const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${apiKey}`;
    const geminiRes = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!geminiRes.ok) {
      const errText = await geminiRes.text();
      console.error("Gemini API Error:", geminiRes.status, errText);
      return res.status(502).json({ error: "processing_failed" });
    }

    const data = await geminiRes.json();
    const candidateText = data.candidates?.[0]?.content?.parts?.[0]?.text;
    if (!candidateText) {
      return res.status(502).json({ error: "empty_response" });
    }

    const parsed = JSON.parse(candidateText);
    let suggestedIsland = parsed.suggestedIsland;
    let suggestedTab = parsed.suggestedTab;

    if (suggestedIsland && ["none", "null", ""].includes(String(suggestedIsland).toLowerCase())) {
      suggestedIsland = null;
    }
    if (suggestedIsland) {
      const ql = question.toLowerCase();
      const asksCurrent = ["this island", "this reef", "current island", "selected reef", "here", "it doing"].some(p => ql.includes(p));
      if (!ql.includes(suggestedIsland.toLowerCase()) && !asksCurrent) {
        suggestedIsland = null;
      }
    }
    if (suggestedTab && ["none", "null", ""].includes(String(suggestedTab).toLowerCase())) {
      suggestedTab = null;
    }

    return res.status(200).json({
      title: parsed.title || "ReefSafe Copilot",
      sections: parsed.sections || [],
      links: parsed.links || [],
      pose: parsed.pose || "answer",
      suggestedIsland,
      suggestedTab
    });
  } catch (error) {
    console.error("Handler error:", error);
    return res.status(500).json({ error: "internal_error" });
  }
};
