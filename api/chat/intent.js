const MODEL = "gemini-3.1-flash-lite";

const INTENTS = [
  "island_status",
  "highest_priority",
  "compare_islands",
  "greener_alternative",
  "dashboard_summary",
  "model_selection",
  "methodology",
  "validation",
  "model_features",
  "dataset_sources",
  "economy_potential_source",
  "reef_economy_calculation",
  "season_rest_calculation",
  "coral_cover_calculation",
  "stress_contribution",
  "actionable_insight",
  "demo_promotion",
  "limitations",
  "problem_scope_sdg",
  "data_quality",
  "data_integration",
  "dashboard_design",
  "implementation_impact",
  "commercial_scalability",
  "innovation",
  "evidence_tab",
  "model_input_coverage",
  "external_live_info",
  "unknown"
];

const INTENT_SCHEMA = {
  type: "object",
  properties: {
    intent: { type: "string", enum: INTENTS },
    islands: {
      type: "array",
      items: { type: "string" },
      maxItems: 2
    },
    confidence: { type: "number" }
  },
  required: ["intent", "islands", "confidence"]
};

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", ["POST"]);
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { question, contextIsland, contextTab } = req.body || {};
  if (!question || typeof question !== "string" || !question.trim()) {
    return res.status(400).json({ error: "invalid_request" });
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return res.status(503).json({ error: "classifier_unavailable" });
  }

  try {
    const prompt = `Classify this user question for the ReefSafe dashboard copilot.
Map typos or paraphrases to the best supported intent.
Reef-adjacent economy means the visitor-spending estimate and uses reef_economy_calculation.
Reef-Adjacent Economy Potential means the separate published RM8.7B valuation and uses economy_potential_source.
Use evidence_tab for questions about Tab 3 or the Evidence tab, and model_input_coverage for completeness of model inputs.
Use season_rest_calculation for the one-month rest or 10-15 year reef-value arithmetic; coral_cover_calculation for the 39.8% mean or 56 surveyed units; stress_contribution for factor contribution arithmetic; actionable_insight for how a recommended check is selected; priority_method for tiers or ranking; uncertainty for prediction ranges.
Use the matching rubric intent for problem/SDG, data quality, data integration, dashboard design, real-world implementation, commercial scalability, or innovation questions.
Examples: 'which plcae is good too visit' => greener_alternative; 'why gradient boosting' => model_selection; 'explaint this dashboard' => dashboard_summary.
Selected island: ${contextIsland || "none"}
Selected tab: ${contextTab || "unknown"}
Question: ${question.trim()}`;

    const payload = {
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: {
        temperature: 0,
        maxOutputTokens: 120,
        responseMimeType: "application/json",
        responseSchema: INTENT_SCHEMA
      }
    };

    const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${apiKey}`;
    const geminiRes = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!geminiRes.ok) {
      return res.status(502).json({ error: "classification_failed" });
    }

    const data = await geminiRes.json();
    const candidateText = data.candidates?.[0]?.content?.parts?.[0]?.text;
    if (!candidateText) {
      return res.status(502).json({ error: "empty_response" });
    }

    const parsed = JSON.parse(candidateText);
    return res.status(200).json({
      intent: parsed.intent || "unknown",
      islands: parsed.islands || [],
      confidence: typeof parsed.confidence === "number" ? parsed.confidence : 0.5
    });
  } catch (error) {
    console.error("Intent handler error:", error);
    return res.status(500).json({ error: "internal_error" });
  }
};
