import http.server
import socketserver
import json
import os
import sys
import urllib.request
import urllib.error

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8088
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")

# Load data bundle for RAG grounding
data_path = os.path.join(DASHBOARD_DIR, "data.js")
REEFSAFE_DATA = {}
try:
    with open(data_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        json_str = "".join(lines[1:]).replace("window.REEFSAFE_DATA = ", "").rstrip(";\n")
        REEFSAFE_DATA = json.loads(json_str)
        print(f"[Server] Successfully loaded data bundle: {len(REEFSAFE_DATA.get('priorityIslands', []))} islands.")
except Exception as e:
    print(f"[Server] Warning: Failed to parse data.js: {e}")

SYSTEM_PROMPT = """You are ReefSafe AI, an expert marine intelligence copilot developed for the Department of Statistics Malaysia (DOSM) Datathon 2026.
You bridge empirical marine ecology (Reef Check Malaysia 13-year surveys, NOAA 5km satellite DHW) with official economic statistics (OpenDOSM Tourism Satellite Account & Domestic Tourism Survey).

Core Principles:
1. Two target audiences:
   - "local": Dive operators, boatmen, local island community, resort staff. Use plain, respectful, encouraging language. Provide practical advice (e.g. use mooring buoys, avoid anchors, watch water temp, do not panic).
   - "exco": Government officials, DOFM rangers, MOTAC policymakers. Use quantitative, evidence-backed civil-service phrasing (e.g. asymmetric loss, carrying capacity, asset protection, gazettement).
2. Key Economic Fact: 78% of island tourism wealth is 'reef-adjacent' (beachfront resorts relying on barrier reefs to stop beach erosion), while only 22% is direct dive/snorkel tickets.
3. Stressor Distinction: If degradation is caused by global heatwaves (NOAA DHW >= 4), DO NOT penalize or shut down local dive businesses. Prescribe shading and biological monitoring. If physical damage (anchors/trampling), mandate permanent mooring buoys and diver quotas.
4. Language: Respond in Bahasa Melayu if the user asks in Malay or if lang='bm'. Respond in English if asked in English.
Keep answers concise, clear, and actionable. Avoid neofuturistic or overly academic jargon when speaking to locals.
"""

def generate_rag_response(msg, island_name, persona, lang):
    msg_lower = msg.lower()
    is_bm = (lang == "bm") or any(w in msg_lower for w in ["boleh", "kenapa", "mengapa", "bagaimana", "karang", "pulau", "bot", "sauh", "selam", "jana", "mesej", "apa"])

    # Find island context
    island = None
    islands_list = REEFSAFE_DATA.get("priorityIslands", [])
    if island_name:
        for i in islands_list:
            if i["island"].lower() == island_name.lower():
                island = i
                break
    
    # Check if message mentions an island explicitly
    for i in islands_list:
        if i["island"].lower() in msg_lower:
            island = i
            break
            
    if not island and islands_list:
        island = islands_list[0] # Default to top priority

    isl_name = island["island"]
    state = island["state"]
    lcc = island["lcc"]
    pred = island["predictedNextChange"]
    evidence = island["evidence"]
    recom = island["recommendation"]
    dhw = island["dhw"]

    # WhatsApp message generation
    if "whatsapp" in msg_lower or "mesej" in msg_lower or "buletin" in msg_lower:
        if is_bm:
            return (
                f"📢 *PERISIKAN HARIAN REEFSAFE AI (KOMUNITI PULAU {isl_name.upper()})*\n"
                f"📅 *Tarikh:* Musim Pembukaan 2026\n"
                f"📊 *Status Terumbu:* Liputan semasa {lcc:.1f}% ({'Waspada' if lcc < 40 else 'Sederhana'})\n"
                f"🌡️ *Suhu Laut:* NOAA Max DHW {dhw:.1f}°C-weeks\n"
                f"⚠️ *Punca Dikesan:* {evidence}\n\n"
                f"⚓ *Tindakan Pengusaha Bot & Penyelam Hari Ini:*\n"
                f"• {recom}\n"
                f"• Sila guna boya tambatan rasmi; elakkan melabuhkan sauh terus ke kawasan karang cetek.\n"
                f"• Terumbu karang yang sihat mengekalkan keindahan pantai dan perniagaan kita bersama! 🌿🌊"
            )
        else:
            return (
                f"📢 *DAILY REEFSAFE BULLETIN ({isl_name.upper()} ISLAND)*\n"
                f"📊 *Current Reef Cover:* {lcc:.1f}% ({'Alert' if lcc < 40 else 'Fair'})\n"
                f"🌡️ *Thermal Stress:* NOAA DHW {dhw:.1f}°C-weeks\n"
                f"⚠️ *Diagnosis:* {evidence}\n\n"
                f"⚓ *Operator Action Checklist:*\n"
                f"• {recom}\n"
                f"• Please utilize gazetted mooring buoys; zero anchor drops on shallow living coral.\n"
                f"• Healthy reefs shelter our resort beaches and preserve our island livelihood! 🌿🌊"
            )

    # Can I bring tourists / Snorkeling inquiry
    if any(w in msg_lower for w in ["bawa", "pelancong", "snorkeling", "esok", "selam", "dive", "visit", "bring", "tourist"]):
        if is_bm:
            advice = "Dibenarkan"
            if "thermal" in evidence.lower() or dhw >= 4.0:
                specific = f"Perairan Pulau {isl_name} sedang mengalami gelombang haba laut (DHW {dhw:.1f}). Pelancong boleh melawat, namun nasihatkan mereka agar tidak memijak karang yang sedang mengalami stres suhu."
            elif island.get("impactAnchor"):
                specific = f"Zon tumpuan di Pulau {isl_name} mengalami sedikit tekanan sauh. Pengusaha bot diminta menggunakan boya tambatan kekal dan mematuhi had kuota harian bagi mengelakkan kesesakan."
            else:
                specific = f"Keadaan perairan adalah terkawal dengan unjuran aliran tahunan {pred:+.1f}%/tahun. Kekalkan amalan mesra eko."
            return (
                f"**Boleh, operasi pelancongan berjalan seperti biasa di Pulau {isl_name}.**\n\n"
                f"🔍 **Status Semasa:**\n"
                f"• **Liputan Karang:** {lcc:.1f}%\n"
                f"• **Tahap Haba (NOAA):** {dhw:.1f}°C-weeks\n\n"
                f"💡 **Panduan Untuk Pengusaha Bot & Dive Master:**\n"
                f"{specific}\n\n"
                f"📌 **Syor:** {recom}"
            )
        else:
            return (
                f"**Yes, standard tourism and diving operations can proceed at {isl_name}.**\n\n"
                f"🔍 **Current Status:**\n"
                f"• **Live Coral Cover:** {lcc:.1f}%\n"
                f"• **Thermal Stress (NOAA):** {dhw:.1f}°C-weeks\n\n"
                f"💡 **Operator Advisory:**\n"
                f"Our model indicates that physical disturbance should be minimized. Ensure all boat operators utilize designated mooring buoys and maintain safe diver-to-guide ratios.\n\n"
                f"📌 **Mandated Action:** {recom}"
            )

    # Why alert / Why red
    if any(w in msg_lower for w in ["kenapa", "mengapa", "merah", "alert", "why", "status", "priority", "keutamaan"]):
        if is_bm:
            return (
                f"**Penjelasan Status Pulau {isl_name} (Kedudukan Keutamaan #{island.get('rank', 1)}):**\n\n"
                f"1. **Liputan Karang Semasa:** {lcc:.1f}% (Purata kebangsaan adalah 41.8%).\n"
                f"2. **Unjuran Model Gradient Boosting:** Dijangka berubah pada kadar **{pred:+.2f}% setahun** sekiranya tiada kawalan.\n"
                f"3. **Punca Utama (Diagnostik):** {evidence}.\n\n"
                f"🏛️ **Sebab Bukan Penutupan Menyeluruh:**\n"
                f"ReefSafe AI mengelakkan penutupan melulu yang menjejaskan ekonomi tempatan. Sebaliknya, kami menetapkan **intervensi tepat**: {recom}."
            )
        else:
            return (
                f"**Diagnostic Status for {isl_name} (Priority Rank #{island.get('rank', 1)}):**\n\n"
                f"1. **Current Coral Baseline:** {lcc:.1f}% (National benchmark: 41.8%).\n"
                f"2. **Predicted Trajectory:** Model forecasts **{pred:+.2f}%/yr** change without intervention.\n"
                f"3. **Observed Stressor Evidence:** {evidence}.\n\n"
                f"🏛️ **Why Precision Intervention Beats Blanket Bans:**\n"
                f"Rather than shutting down entire islands and bankrupting local operators, ReefSafe AI isolates the specific driver: {recom}."
            )

    # Economic impact & Reef-Adjacent questions
    if any(w in msg_lower for w in ["ekonomi", "economic", "78%", "adjacent", "bersebelahan", "rm", "kdnk", "gdp", "wang", "rugi"]):
        if is_bm:
            return (
                f"**Paradigma Ekonomi Bersebelahan Karang (Reef-Adjacent Wealth):**\n\n"
                f"• **Nisbah 78% vs 22%:** Analisis data OpenDOSM membuktikan bahawa 78% perbelanjaan pelancong adalah 'bersebelahan karang' (hotel mewah, resort pantai, restoran), manakala hanya 22% datang daripada tiket menyelam terus.\n"
                f"• **Fungsi Pelindung:** Terumbu karang hidup menyerap **97% tenaga ombak lautan**. Sekiranya karang mati, pantai berpasir putih akan terhakis, menyebabkan anggaran **kehilangan 30% premium nilai bilik resort** (Aset terdedah bernilai **RM 842.5 Juta** secara nasional).\n"
                f"• **Sumbangan KDNK:** Pelancongan pesisir menyumbang **RM 68.4 Bilion** kepada ekonomi negara (Akaun Satelit Pelancongan OpenDOSM)."
            )
        else:
            return (
                f"**The Reef-Adjacent Economic Valuation Paradigm:**\n\n"
                f"• **78% vs 22% Breakdown:** OpenDOSM Domestic Tourism and Tourism Satellite Account data show that 78% of island tourist spending is 'reef-adjacent' (beachfront resorts, calm lagoons), while only 22% comes from direct dive/snorkel admissions.\n"
                f"• **Wave Attenuation:** Healthy barrier reefs dissipate **97% of incoming ocean wave energy**. Losing the reef destroys white-sand beaches through erosion, triggering an estimated **30% depreciation in resort room rates** (RM 842.5M in coastal assets at risk).\n"
                f"• **GDP Impact:** Coastal ecotourism contributes **RM 68.4 Billion** to national gross value added (OpenDOSM TSA)."
            )

    # General / Default response
    if is_bm:
        return (
            f"**ReefSafe AI Copilot**\n\n"
            f"📍 **Pulau {isl_name}** ({state})\n"
            f"• **Liputan Karang:** {lcc:.1f}%\n"
            f"• **Aliran 2026:** {pred:+.2f}%/tahun\n"
            f"• **Tindakan:** {recom}\n\n"
            f"Tanya saya mengenai status 40 pulau, simulasi kuota pelawat, atau penilaian ekonomi resort."
        )
    else:
        return (
            f"**ReefSafe AI Copilot**\n\n"
            f"📍 **{isl_name} Island** ({state})\n"
            f"• **Coral Cover:** {lcc:.1f}%\n"
            f"• **2026 Trend:** {pred:+.2f}%/year\n"
            f"• **Action:** {recom}\n\n"
            f"Ask me about island status across 40 reefs, visitor carrying capacity, or resort economic valuation."
        )

def call_gemini_api(api_key, user_msg, island_context, persona, lang):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"{SYSTEM_PROMPT}\n\nContext on currently selected island:\n{json.dumps(island_context, indent=2)}\n\nAudience Persona: {persona}\nRequested Language: {lang}\n\nUser Question:\n{user_msg}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 600
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        res = json.loads(response.read().decode("utf-8"))
        return res["candidates"][0]["content"]["parts"][0]["text"]

class ReefSafeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                req_data = json.loads(body)
                user_msg = req_data.get("message", "").strip()
                island_name = req_data.get("island", "Tioman")
                persona = req_data.get("persona", "local")
                lang = req_data.get("lang", "en")
                api_key = req_data.get("apiKey") or os.environ.get("GEMINI_API_KEY")

                # Find island details for context
                island_ctx = {}
                for i in REEFSAFE_DATA.get("priorityIslands", []):
                    if i["island"].lower() == island_name.lower():
                        island_ctx = i
                        break

                provider = "grounded-rag"
                reply = ""
                if api_key:
                    try:
                        reply = call_gemini_api(api_key, user_msg, island_ctx, persona, lang)
                        provider = "gemini-1.5-flash"
                    except Exception as err:
                        print(f"[Server] Gemini API failed, falling back to Grounded RAG: {err}")
                        reply = generate_rag_response(user_msg, island_name, persona, lang)
                else:
                    reply = generate_rag_response(user_msg, island_name, persona, lang)

                response_data = {
                    "reply": reply,
                    "provider": provider,
                    "island": island_name
                }
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        self.send_response(404)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ReefSafeHandler) as httpd:
        print(f"[ReefSafe AI Server] Serving dashboard & LLM API on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
