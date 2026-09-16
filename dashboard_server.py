"""Serve ReefSafe and classify chat questions without exposing API keys."""

import http.server
import json
import os
import sys
import time
import urllib.request
from functools import partial
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODEL = "gemini-3.1-flash-lite"
INTENTS = (
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
    "priority_method",
    "uncertainty",
    "problem_scope_sdg",
    "data_quality",
    "data_integration",
    "dashboard_design",
    "implementation_impact",
    "commercial_scalability",
    "innovation",
    "evidence_tab",
    "model_input_coverage",
    "demo_promotion",
    "limitations",
    "external_live_info",
    "unsupported",
)


def classify_question(question, context_island, api_key, urlopen=urllib.request.urlopen, context_tab=None):
    schema = {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": list(INTENTS),
                "description": "The single ReefSafe capability requested; travel destination recommendations always use greener_alternative and never model_selection.",
            },
            "islands": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number"},
        },
        "required": ["intent", "islands", "confidence"],
    }
    prompt = (
        "Classify this ReefSafe dashboard question. Correct spelling mistakes and paraphrases. "
        "Return only the schema fields. Use highest_priority for the reef with the greatest "
        "screening urgency; risk never means visitor safety. Use external_live_info for live "
        "weather, bookings, official or live promotions, travel advisories, or medical diving safety. "
        "Use demo_promotion for a general promotion request or an explicit mock/demo promotion; it is "
        "a fictional non-bookable concept. "
        "Use greener_alternative whenever the user asks which place, island, reef, or destination "
        "is good or better to visit, even with spelling mistakes. Use model_selection only for "
        "questions about Gradient Boosting, model choice, accuracy, or baseline comparison. "
        "Choose the narrowest calculation or judging topic instead of generic methodology. "
        "Reef-adjacent economy means the visitor-spending estimate and uses reef_economy_calculation. "
        "Reef-Adjacent Economy Potential means the separate published RM8.7B valuation and uses "
        "economy_potential_source. Use evidence_tab for questions about Tab 3 or the Evidence tab, "
        "and model_input_coverage for the completeness of model inputs. "
        "Use season_rest_calculation for the one-month rest or 10-15 year reef-value arithmetic; "
        "coral_cover_calculation for the 39.8% mean or 40 surveyed units; stress_contribution for "
        "factor contribution arithmetic; actionable_insight for how a recommended check is selected; "
        "priority_method for tiers or ranking; uncertainty for prediction ranges. Use the matching "
        "rubric intent for problem/SDG, data quality, data integration, dashboard design, real-world "
        "implementation, commercial scalability, or innovation questions. "
        "Examples: 'which plcae is good too visit' => greener_alternative; "
        "'why gradient boosting' => model_selection; 'explaint this dashboard' => dashboard_summary; "
        "'how the stress factor contribution is calculated' => stress_contribution. "
        f"Selected island: {context_island or 'none'}\n"
        f"Selected tab: {context_tab or 'unknown'}\nQuestion: {question}"
    )
    body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 120,
                "responseMimeType": "application/json",
                "responseSchema": schema,
            },
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    with urlopen(request, timeout=8) as response:
        payload = json.loads(response.read())
    text = payload["candidates"][0]["content"]["parts"][0]["text"]
    result = json.loads(text)
    if result.get("intent") not in INTENTS:
        raise ValueError(f"Unsupported intent: {result.get('intent')}")
    islands = result.get("islands")
    confidence = result.get("confidence")
    if not isinstance(islands, list) or len(islands) > 2 or not all(isinstance(name, str) for name in islands):
        raise ValueError("Invalid islands")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValueError("Invalid confidence")
    return {"intent": result["intent"], "islands": islands, "confidence": confidence}


REEFY_SYSTEM_INSTRUCTION = (
    "You are Reefy, the institutional AI copilot for the ReefSafe dashboard (DOSM Datathon 2026).\n"
    "Respond with high data-ink ratio: provide a clear title and structured, labeled sections with concise facts, "
    "matching the institutional OpenDOSM / Gov.uk design standard. Never hallucinate outside sources (e.g. Green Fins, sunscreen, plastics).\n\n"
    "OFFICIAL DATASETS & SOURCES (from data source.pdf & DATA_PROVENANCE.md):\n"
    "1. Reef Check Malaysia (RCM):\n"
    "   * 19 Annual Survey Reports (2007-2025), 404 monitoring-unit rows of standardized 100m transects.\n"
    "   * Scored ML model input: live coral cover (LCC), disturbance & pollution indicators, fish/invertebrate counts.\n"
    "   * Link: {'label': 'Reef Check Malaysia annual reports', 'href': 'https://reefcheck.org.my/annualsurveyreports/'}\n"
    "2. Department of Statistics Malaysia (DOSM) & data.gov.my:\n"
    "   * State Real GDP Supply (Accommodation, F&B, Transport): https://data.gov.my/data-catalogue/gdp_state_real_supply\n"
    "   * Marine Fish Landings by State (Resource pressure proxy from Department of Fisheries): https://data.gov.my/data-catalogue/fish_landings\n"
    "   * River Basin Water Quality & Pollution (Runoff indicators from Dept of Environment: BOD, ammoniacal nitrogen, suspended solids): https://data.gov.my/data-catalogue/water_pollution_basin\n"
    "   * Marine Park Visitors 2000-2017: Official series from archive.data.gov.my across Johor, Kedah, Pahang, Terengganu, and Labuan.\n"
    "   * Domestic Tourism Survey 2024: RM410 average expenditure per visitor.\n"
    "   * OpenDOSM Portal: {'label': 'OpenDOSM Data Catalogue', 'href': 'https://open.dosm.gov.my'}\n"
    "   * Link: {'label': 'DOSM Domestic Tourism Survey 2024', 'href': 'https://www.dosm.gov.my/portal-main/release-content/domestic-tourism-survey-2024'}\n"
    "3. NOAA Coral Reef Watch (U.S. NESDIS / NOAA):\n"
    "   * 5km Satellite Virtual Stations Time-Series: Daily sea surface temperature and Degree Heating Weeks (DHW).\n"
    "   * Status: Kept outside the scored ML model as regional environmental context only.\n"
    "   * Link: {'label': 'NOAA Coral Reef Watch', 'href': 'https://coralreefwatch.noaa.gov/product/vs/data.php'}\n"
    "4. Geospatial & Marine Park Administration:\n"
    "   * Department of Survey and Mapping Malaysia (JUPEM): Official geodetic authority for island coordinates and territorial baseline boundaries. Link: {'label': 'JUPEM Geodetic Portal', 'href': 'https://www.jupem.gov.my'}\n"
    "   * Department of Fisheries Malaysia (DOFM) – Marine Parks Section: Official regulatory register of gazetted Marine Parks and Fishery Prohibited Areas. Link: {'label': 'DOFM Marine Parks', 'href': 'https://www.dof.gov.my'}\n"
    "5. Economic Valuation Benchmark:\n"
    "   * Department of Marine Park Malaysia (DMPM 2011-2015 study), Total Economic Value of Marine Biodiversity: Malaysia Marine Parks.\n"
    "   * RM8.7 Billion/year Total Economic Value (TEV) benchmark across 6 archipelagos (Payar, Perhentian, Redang, Tioman, Tinggi, Labuan), based on 7 ecosystem components (largely non-market willingness-to-pay).\n"
    "   * Link: {'label': 'Marine biodiversity economic valuation', 'href': 'https://wdpa.s3.amazonaws.com/Country_informations/MYS/TOTAL%20ECONOMIC%20VALUE%20OF%20MARINE%20BIODIVERSITY.pdf'}\n\n"
    "KEY CONCEPTS & DEFINITIONS (DO NOT CONFUSE THESE):\n"
    "- 'Season Rest vs Long-Term Reef Revenue':\n"
    "  * Concept: Annual 4–5 month closure during the Northeast Monsoon (Nov–March) when tourist boats stop and marine parks rest.\n"
    "  * 1-month revenue loss proxy: ~RM5.01M for 1 month of closure (RM60.09M annual visitor spending / 12 months).\n"
    "  * Long-term reef value: RM60.09M/yr protected reef-adjacent economy (RM601M over 10 yrs, RM901M over 15 yrs undiscounted).\n"
    "  * Tradeoff ratio: 12x to 18x (the long-term reef value outweighs the 1-month seasonal closure disruption by 12–18 times).\n"
    "- 'Reef-Adjacent Economy': The RM60.09M/year annual visitor spending proxy. Formula: 1,464,770 annual visitors * RM410 avg spend (DOSM 2024) * 10% reef-attributable share (Spalding et al. 2017). Covers 30 of 40 units across 4 marine parks.\n"
    "- 'Reef-Adjacent Economy Potential': The historical RM8.7 Billion/year Total Economic Value (TEV) published benchmark by DMPM (2011-2015) for the six evaluated marine-park archipelagos. This is a total economic capital benchmark (mostly existence/bequest value), NOT annual tourism revenue or commercial cash flow.\n"
    "- 'Stress Factor Contribution': Feature importance attribution calculated via Tree-Path Decomposition (Saabas 2014) through the Gradient Boosting Regressor. Traces decision splits to feature groups (Substrate, Fish, Reported Impacts, Prior Cover, Geography). Baseline + factor contributions = predicted next change. It is NOT NOAA DHW!\n"
    "- 'Top 10 Priority Islands': 1. Labuan (-14.42 pp/yr), 2. Kapas (-5.75 pp/yr), 3. Seri Buat (-5.15 pp/yr), 4. Mertang (-5.03 pp/yr), 5. Mensirip (-4.85 pp/yr), 6. Tenggol (-4.64 pp/yr), 7. Tinggi (-4.63 pp/yr), 8. Lima (-4.37 pp/yr), 9. Sibu (-4.34 pp/yr), 10. Lankayan (-4.07 pp/yr). These represent the 25% highest screening priority queue for urgent field verification.\n"
    "- 'Greener Alternative' / 'Green Status': In ReefSafe, 'green' means a monitoring unit with a predicted non-negative change (>= 0 pp/yr, tier Monitor). Only Kapalai (+0.77 pp/yr) and Malacca (+3.48 pp/yr) have green status. Kapalai is the only verified visitor destination with a non-negative signal. Never hallucinate Green Fins, sunscreen, or unrelated travel guidelines.\n"
    "- 'National Coral Cover KPI': 39.8% arithmetic mean live coral cover across 40 monitoring units surveyed in 2025.\n"
    "- 'ML Model Performance': Gradient Boosting Regressor, MAE 5.862 pp/yr (2.1% improvement over baseline), 95% pooled forward-test residual distribution [-16.25, +13.66 pp/yr].\n\n"
    "CRITICAL STYLE & FORMATTING RULES (HIGH DATA-INK RATIO):\n"
    "1. Simple Sentences & Point Form: Write in clear, short, simple sentences. Format details as bullet points ('• ' or '- '). Keep each bullet point to 1 concise sentence. Avoid long descriptive paragraphs.\n"
    "2. Be Direct & Answer ONLY What Was Asked: Strictly avoid unnecessary answers or irrelevant background that does not answer the user's specific question.\n"
    "   * If asked about 'season rest', explain season rest, the 1-month loss proxy, and the 12–18x long-term tradeoff. DO NOT mention Labuan or Tree-Path Decomposition!\n"
    "   * If asked 'how reef adjacent economy', explain the definition, formula, and RM60.09M estimate. DO NOT mention Labuan, TEV, or priority rankings unless specifically asked!\n"
    "   * If asked 'how is Tioman' (or any specific island), answer ONLY about that island's status and trends. DO NOT mention Labuan or other islands unless the user asked for a comparison!\n"
    "3. Structure: Return a short, descriptive 'title' and 1 to 2 focused 'sections' (maximum 3 only if comparing two islands) with uppercase labels (e.g. 'SUMMARY', 'FORMULA', 'TRADEOFF', 'STATUS', 'METHODOLOGY').\n"
    "4. Dropdown Island Guardrail: The active dropdown island is ONLY for resolving ambiguous references like 'how is this reef' or 'here'. If the user's question is a general concept or mentions an island, COMPLETELY IGNORE the dropdown island.\n"
    "5. Commercial & Safety Guardrail: Never fabricate commercial packages or hotel deals. Never rate islands as 'safe' or 'unsafe' for tourists; screening priority measures biological monitoring urgency, not human safety risks.\n"
    "6. If asked about datasets or sources, cite the exact official sources from the list above.\n"
    "7. Multi-turn Awareness: Follow-up questions like 'how it is calculated' refer to the topic discussed in the previous turn.\n"
)

CHAT_REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["label", "text"],
            },
        },
        "links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "href": {"type": "string"},
                },
                "required": ["label", "href"],
            },
        },
        "pose": {"type": "string", "enum": ["answer", "happy", "warn", "wave"]},
        "suggestedIsland": {"type": "string"},
        "suggestedTab": {"type": "string", "enum": ["overview", "diagnostics", "evidence"]},
    },
    "required": ["title", "sections", "pose"],
}


def generate_chat_reply(question, context_island, api_key, urlopen=urllib.request.urlopen, context_tab=None, history=None):
    contents = []
    if history and isinstance(history, list):
        for item in history[-6:]:
            role = "user" if item.get("role") == "user" else "model"
            text = item.get("text", "")
            if text:
                contents.append({"role": role, "parts": [{"text": text}]})

    current_prompt = (
        f"User question: {question}\n"
        f"Active island in dropdown: {context_island or 'none'}\n"
        f"Active tab: {context_tab or 'overview'}\n"
        f"INSTRUCTION: Answer ONLY the user question directly. Write simple sentences in point form. "
        f"In each section, format the 'text' as 2 to 3 bullet points separated by newlines starting with '• ' (e.g. '• First point.\\n• Second point.'). "
        f"Do NOT mention the dropdown island ({context_island}) unless the user specifically asked about it."
    )
    contents.append({"role": "user", "parts": [{"text": current_prompt}]})

    body = json.dumps(
        {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": REEFY_SYSTEM_INSTRUCTION}]},
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1000,
                "responseMimeType": "application/json",
                "responseSchema": CHAT_REPLY_SCHEMA,
            },
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    payload = None
    for attempt in range(2):
        try:
            with urlopen(request, timeout=25) as response:
                payload = json.loads(response.read())
            break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as err:
            if attempt == 0:
                time.sleep(1.0)
                continue
            raise
    if not payload:
        raise ValueError("Empty response from language model")
    text = payload["candidates"][0]["content"]["parts"][0]["text"]
    result = json.loads(text)
    title = result.get("title", "ReefSafe Copilot")
    sections = result.get("sections", [])
    links = result.get("links", [])
    pose = result.get("pose", "answer")
    suggested_island = result.get("suggestedIsland")
    suggested_tab = result.get("suggestedTab")
    if suggested_island and str(suggested_island).lower() in ("none", "null", ""):
        suggested_island = None
    if suggested_island:
        ql = question.lower()
        asks_current = any(p in ql for p in ("this island", "this reef", "current island", "selected reef", "here", "it doing"))
        if suggested_island.lower() not in ql and not asks_current:
            suggested_island = None
    if suggested_tab and str(suggested_tab).lower() in ("none", "null", ""):
        suggested_tab = None
    return {
        "title": title,
        "sections": sections,
        "links": links,
        "pose": pose,
        "suggestedIsland": suggested_island,
        "suggestedTab": suggested_tab,
    }


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path not in ("/api/chat", "/api/chat/intent"):
            self.send_json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > 8192:
                raise ValueError("Invalid request size")
            payload = json.loads(self.rfile.read(length))
            question = payload.get("question", "")
            context_island = payload.get("contextIsland")
            context_tab = payload.get("contextTab")
            history = payload.get("history")
            if not isinstance(history, list):
                history = []
            if not isinstance(question, str) or not question.strip() or len(question) > 240:
                raise ValueError("Invalid question")
            if context_island is not None and not isinstance(context_island, str):
                raise ValueError("Invalid context")
            if context_tab not in (None, "overview", "diagnostics", "evidence", "science"):
                raise ValueError("Invalid tab context")
        except (ValueError, json.JSONDecodeError):
            self.send_json(400, {"error": "invalid_request"})
            return

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self.send_json(503, {"error": "classifier_unavailable"})
            return
        try:
            if self.path == "/api/chat":
                result = generate_chat_reply(
                    question.strip(),
                    context_island,
                    api_key,
                    context_tab=context_tab,
                    history=history,
                )
            else:
                result = classify_question(question.strip(), context_island, api_key, context_tab=context_tab)
        except Exception as error:
            print(f"Gemini chat processing failed: {error}", file=sys.stderr)
            self.send_json(502, {"error": "processing_failed"})
            return
        self.send_json(200, result)


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8088))
    handler = partial(NoCacheHandler, directory=ROOT / "dashboard")
    with http.server.ThreadingHTTPServer((host, port), handler) as server:
        print(f"ReefSafe dashboard: http://{host}:{port}")
        server.serve_forever()
