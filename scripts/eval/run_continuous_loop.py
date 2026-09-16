import os
import sys
import time
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import dashboard_server

api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable is required.", file=sys.stderr)
    sys.exit(1)

QUESTION_BATTERY = [
    # --- Category 1: Technical & Model Methodology ---
    ("Technical", "explain the gradient boosting regressor hyperparameters and validation MAE", "Labuan", "evidence"),
    ("Technical", "how is Tree-Path Decomposition (Saabas 2014) calculated for factor attribution", "Redang", "diagnostics"),
    ("Technical", "what is the 95% pooled forward test residual distribution and how is uncertainty quantified", "Tioman", "evidence"),
    ("Technical", "why is NOAA DHW excluded from the scored model features", "Kapas", "diagnostics"),
    ("Technical", "what are the feature groups used in the coral cover prediction model", "Labuan", "overview"),

    # --- Category 2: Policy, Economics & Governance ---
    ("Policy & Econ", "what is the difference between Reef-Adjacent Economy and Reef-Adjacent Economy Potential", "Redang", "overview"),
    ("Policy & Econ", "how is the RM60.09M annual spending proxy calculated", "Tioman", "overview"),
    ("Policy & Econ", "explain the RM8.7B Total Economic Value study by DMPM", "Labuan", "evidence"),
    ("Policy & Econ", "how does ReefSafe align with SDG 14 Life Below Water", "Redang", "overview"),
    ("Policy & Econ", "what action should a marine park ranger take when an island is in the top 25% screening queue", "Kapas", "diagnostics"),

    # --- Category 3: Levels & Priority Lists (Testing List Formatting) ---
    ("List / Ranking", "top 10 island", "Labuan", "overview"),
    ("List / Ranking", "give me the top 5 highest priority reefs needing immediate field survey", "Redang", "overview"),
    ("List / Ranking", "list the 4 covered marine parks in the economic valuation", "Tioman", "overview"),
    ("List / Ranking", "rank the islands by predicted coral decline", "Labuan", "diagnostics"),

    # --- Category 4: Casual & Daily Conversations ---
    ("Casual", "good morning Reefy, how are you today?", "Redang", "overview"),
    ("Casual", "who are you and what can you help me with?", "Tioman", "overview"),
    ("Casual", "what is your favourite coral reef in Malaysia?", "Redang", "overview"),
    ("Casual", "do fishes sleep at night in coral reefs?", "Kapas", "overview"),
    ("Casual", "thank you Reefy, you are very helpful!", "Labuan", "overview"),

    # --- Category 5: Travel, Booking & Safety Checks ---
    ("Travel & Safety", "which island is good to visit for a holiday?", "Redang", "overview"),
    ("Travel & Safety", "Suggest a greener alternative", "Labuan", "overview"),
    ("Travel & Safety", "can I book a diving resort package through ReefSafe?", "Tioman", "overview"),
    ("Travel & Safety", "is Labuan safe to swim and dive right now?", "Labuan", "overview"),
    ("Travel & Safety", "do you have any discount promotions for Tioman?", "Tioman", "overview"),

    # --- Category 6: Random, Trivia & Out-of-Domain ---
    ("Out-of-Domain", "can I eat coral reef with sambal?", "Redang", "overview"),
    ("Out-of-Domain", "what is the recipe for chocolate brownies?", "Labuan", "overview"),
    ("Out-of-Domain", "write a python function to sort a list of numbers", "Tioman", "overview"),
    ("Out-of-Domain", "who is the current Prime Minister of Malaysia?", "Redang", "overview"),
    ("Out-of-Domain", "what is the price of Bitcoin today?", "Labuan", "overview"),

    # --- Category 7: Nonsense, Gibberish & Edge Cases ---
    ("Nonsense", "asdkjfh192837 zxcvbnm ???", "Labuan", "overview"),
    ("Nonsense", "1111111111111111111111", "Redang", "overview"),
    ("Nonsense", "!@#$%^&*()_+", "Tioman", "overview"),
    ("Nonsense", "why is the sky blue and fish green", "Kapas", "overview"),
]

def run_test_battery(start_idx=0, count=10):
    selected = QUESTION_BATTERY[start_idx:start_idx + count]
    print(f"\n======================================================================")
    print(f"  RUNNING CONTINUOUS QUESTION EVALUATION (Questions {start_idx+1} to {start_idx+len(selected)})")
    print(f"======================================================================\n")

    for i, (category, question, island, tab) in enumerate(selected, start_idx + 1):
        print(f">>> [{i:02d}] CATEGORY: {category}")
        print(f"    QUESTION: \"{question}\" (Context: {island}, Tab: {tab})")
        
        t0 = time.time()
        try:
            reply = dashboard_server.generate_chat_reply(
                question, island, api_key, context_tab=tab
            )
            elapsed = time.time() - t0
            
            title = reply.get("title", "No Title")
            sections = reply.get("sections", [])
            links = [link.get("label") for link in reply.get("links", [])]
            pose = reply.get("pose", "answer")
            s_tab = reply.get("suggestedTab")
            s_island = reply.get("suggestedIsland")

            print(f"    STATUS: SUCCESS ({elapsed:.2f}s) | Pose: {pose} | Tab: {s_tab} | Island: {s_island}")
            print(f"    TITLE: {title}")
            for sec in sections:
                label = sec.get("label", "INFO")
                text = sec.get("text", "")
                # Format text indented
                lines = text.split("\n")
                print(f"    [{label}]:")
                for line in lines:
                    print(f"      {line}")
            if links:
                print(f"    LINKS: {', '.join(links)}")
        except Exception as e:
            print(f"    STATUS: FAILED -> {e}")
        
        print("-" * 70)
        time.sleep(2.5)  # Respect API quota rate limits

if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else len(QUESTION_BATTERY)
    run_test_battery(start, count)
