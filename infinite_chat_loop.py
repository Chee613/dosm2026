import os
import sys
import time
import datetime
import random
import urllib.error
import dashboard_server

api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable is required.", file=sys.stderr)
    sys.exit(1)

ISLANDS = [
    "Labuan", "Redang", "Tioman", "Kapas", "Perhentian", "Payar", "Tinggi", 
    "Kapalai", "Sipadan", "Tenggol", "Lima", "Sibu", "Mertang", "Mensirip", 
    "Seri Buat", "Lang Tengah", "Bidong", "Penyu", "Malacca", "Lankayan"
]

TABS = ["overview", "diagnostics", "evidence"]

QUESTION_TEMPLATES = [
    # 1. Lists & Rankings
    ("List / Ranking", "top 10 island"),
    ("List / Ranking", "give me the top 10 priority islands with predicted decline"),
    ("List / Ranking", "which are the top 5 most urgent reefs for field verification"),
    ("List / Ranking", "rank the islands by live coral cover decline"),
    ("List / Ranking", "list the 4 marine parks covered in the economic valuation"),
    ("List / Ranking", "what are the 5 feature groups used in factor attribution"),
    ("List / Ranking", "give me the priority list for rangers"),

    # 2. Technical & ML
    ("Technical", "explain the gradient boosting regressor hyperparameters and validation MAE"),
    ("Technical", "how is Tree-Path Decomposition (Saabas 2014) calculated for factor attribution"),
    ("Technical", "what is the 95% pooled forward test residual distribution and uncertainty range"),
    ("Technical", "why is NOAA DHW excluded from the scored model features"),
    ("Technical", "how does fold-local median imputation prevent future data leakage"),
    ("Technical", "is this model causal or exploratory screening"),
    ("Technical", "what is the national arithmetic mean live coral cover in 2025"),
    ("Technical", "explain the difference between RCM transect surveys and satellite observations"),

    # 3. Policy & Economics
    ("Policy & Econ", "what is reef adjacent economy"),
    ("Policy & Econ", "what is Reef-Adjacent Economy Potential"),
    ("Policy & Econ", "what is the difference between Reef-Adjacent Economy and Reef-Adjacent Economy Potential"),
    ("Policy & Econ", "how is the RM60.09M annual visitor spending proxy calculated"),
    ("Policy & Econ", "explain the RM8.7B Total Economic Value study by DMPM 2011-2015"),
    ("Policy & Econ", "how does ReefSafe align with SDG 14 Life Below Water"),
    ("Policy & Econ", "what should a marine park ranger do when an island is in high screening priority"),
    ("Policy & Econ", "why is the 10 percent attribution coefficient from Spalding et al. 2017 used"),

    # 4. Travel & Safety
    ("Travel & Safety", "which island is good to visit for a holiday"),
    ("Travel & Safety", "Suggest a greener alternative"),
    ("Travel & Safety", "which island is green"),
    ("Travel & Safety", "is it safe to dive and swim in this reef right now"),
    ("Travel & Safety", "can I book a diving resort package through ReefSafe"),
    ("Travel & Safety", "do you have hotel deals or holiday promotions"),
    ("Travel & Safety", "is Labuan safe for tourists"),

    # 5. Data Provenance & Sources
    ("Provenance", "show me all the dataset"),
    ("Provenance", "what are the sources of data in ReefSafe"),
    ("Provenance", "where can I download the raw Reef Check Malaysia reports"),
    ("Provenance", "how is DOSM data.gov.my data integrated"),
    ("Provenance", "what geospatial authority provides island coordinates"),
    ("Provenance", "any other dataset used?"),

    # 6. Casual & Conversational
    ("Casual", "hello Reefy, who are you?"),
    ("Casual", "good morning, how can you help me today?"),
    ("Casual", "what is your favourite coral reef in Malaysia?"),
    ("Casual", "do fishes sleep at night in coral reefs?"),
    ("Casual", "thank you Reefy, that was super helpful!"),
    ("Casual", "what is the weather like today?"),
    ("Casual", "can you tell me an interesting fact about corals?"),

    # 7. Out-of-Domain & Trivia
    ("Out-of-Domain", "can I eat coral reef with sambal?"),
    ("Out-of-Domain", "what is the recipe for chocolate brownies?"),
    ("Out-of-Domain", "write a python function to invert a binary tree"),
    ("Out-of-Domain", "who is the current Prime Minister of Malaysia?"),
    ("Out-of-Domain", "what is the current price of Bitcoin?"),
    ("Out-of-Domain", "how do I fix a leaking water pipe?"),
    ("Out-of-Domain", "who won the FIFA World Cup in 2022?"),
    ("Out-of-Domain", "what is the capital city of Australia?"),

    # 8. Nonsense, Gibberish & Edge Cases
    ("Nonsense", "asdkjfh192837 zxcvbnm ???"),
    ("Nonsense", "1111111111111111111111"),
    ("Nonsense", "!@#$%^&*()_+"),
    ("Nonsense", "why is the sky blue and fish green"),
    ("Nonsense", "blablabla wubba lubba dub dub"),
    ("Nonsense", "..........................."),
    ("Nonsense", "undefined null NaN"),
]

LOG_FILE = "continuous_chat_eval.log"

def main():
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting ReefSafe Continuous Evaluation Daemon...")
    print(f"Logging outputs to: {os.path.abspath(LOG_FILE)}")
    sys.stdout.flush()

    iteration = 0
    consecutive_429 = 0

    while True:
        iteration += 1
        category, q_text = random.choice(QUESTION_TEMPLATES)
        island = random.choice(ISLANDS)
        tab = random.choice(TABS)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = [f"\n=== [Iter {iteration:04d}] {timestamp} | Category: {category} ==="]
        log_entry.append(f"Question: \"{q_text}\" (Context: {island}, Tab: {tab})")

        t0 = time.time()
        try:
            reply = dashboard_server.generate_chat_reply(
                q_text, island, api_key, context_tab=tab
            )
            elapsed = time.time() - t0
            consecutive_429 = 0

            title = reply.get("title", "No Title")
            sections = reply.get("sections", [])
            links = [l.get("label") for l in reply.get("links", [])]
            pose = reply.get("pose", "answer")

            log_entry.append(f"Response ({elapsed:.2f}s) | Title: {title} | Pose: {pose} | Links: {len(links)}")
            for sec in sections:
                label = sec.get("label", "INFO")
                text = sec.get("text", "")
                log_entry.append(f"  [{label}]: {text}")
            if links:
                log_entry.append(f"  [LINKS]: {', '.join(links)}")

            status_str = f"[{timestamp}] Iter {iteration:04d}: SUCCESS ({elapsed:.1f}s) - '{q_text[:35]}...' -> '{title}'"
            print(status_str)
            sys.stdout.flush()

        except urllib.error.HTTPError as err:
            elapsed = time.time() - t0
            if err.code == 429:
                consecutive_429 += 1
                backoff = min(60, 5 * consecutive_429)
                msg = f"[{timestamp}] Iter {iteration:04d}: RATE LIMITED (HTTP 429). Backing off {backoff}s..."
                print(msg)
                log_entry.append(f"ERROR: {msg}")
                sys.stdout.flush()
                time.sleep(backoff)
            else:
                msg = f"[{timestamp}] Iter {iteration:04d}: HTTP ERROR {err.code}: {err.reason}"
                print(msg)
                log_entry.append(f"ERROR: {msg}")
                sys.stdout.flush()

        except Exception as ex:
            elapsed = time.time() - t0
            msg = f"[{timestamp}] Iter {iteration:04d}: EXCEPTION: {ex}"
            print(msg)
            log_entry.append(f"ERROR: {msg}")
            sys.stdout.flush()

        # Write to log file
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as lf:
                lf.write("\n".join(log_entry) + "\n")
        except Exception:
            pass

        # Healthy delay between queries to respect API quota
        time.sleep(3.5)

if __name__ == "__main__":
    main()
