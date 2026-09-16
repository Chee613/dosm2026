import os
import sys
import json
import time
import dashboard_server

api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable is required.", file=sys.stderr)
    sys.exit(1)

TEST_QUESTIONS = [
    # 1. Levels, Rankings & Top 10 lists
    "top 10 island",
    "give me the top 10 priority",
    "which are the top 5 most urgent reefs",
    "list the top priority units for rangers",
    "rank the islands by coral decline",

    # 2. Economic Definitions & Attribution
    "what is reef adjacent economy",
    "what is Reef-Adjacent Economy Potential",
    "how is the RM60.09M calculated",
    "what is the source of RM8.7B",
    "explain the 10 percent attribution coefficient",

    # 3. Model Logic & Factor Attribution
    "how the Stress factor contribution is calculated",
    "why Gradient Boosting instead of Linear Regression",
    "is this a causal model",
    "what is the model MAE and uncertainty range",
    "what feature groups contribute to the score",

    # 4. Regional Environmental Context & NOAA
    "what is Regional heat stress (NOAA)",
    "what is the finding from the noaa",
    "is NOAA DHW included in the ML model features",
    "how many corals bleached in 2024",

    # 5. Travel, Safety & Green Tier
    "which island is good to visit",
    "Suggest a greener alternative",
    "which island is safe for diving",
    "do you have hotel deals or holiday promotions",
    "is Redang safe right now",

    # 6. Data Sources & Provenance
    "show me all the dataset",
    "where does the coral data come from",
    "what is the source for tourism expenditure",
    "any other dataset used?",
    "what geospatial data is included",

    # 7. Conversational & Ambiguous Queries
    "hello who are you",
    "what can you help me with",
    "what is the findings",
    "explain this dashboard",
    "what should a ranger check first",

    # 8. Out-of-Domain, Trick & Nonsensical Queries
    "can I eat coral reef",
    "what is the price of Bitcoin today",
    "how to bake a chocolate cake",
    "who is the Prime Minister of Malaysia",
    "asdjklhf129837aksjdf",
    "can you write me a python script to hack a website",
    "is coral an animal or a rock",
    "what is the weather tomorrow in London",
]

def run_loop(max_batches=2, delay_sec=1):
    print("=" * 70)
    print("ReefSafe Copilot Automated Professionalism & Variety Loop")
    print(f"Loaded {len(TEST_QUESTIONS)} diverse test cases.")
    print("=" * 70)

    total_tested = 0
    passed = 0

    for batch_idx in range(1, max_batches + 1):
        print(f"\n>>> Starting Batch {batch_idx}/{max_batches} <<<\n")
        for idx, q in enumerate(TEST_QUESTIONS, 1):
            total_tested += 1
            island_ctx = "Labuan" if idx % 2 == 0 else "Redang"
            tab_ctx = "overview" if idx % 3 == 0 else ("diagnostics" if idx % 3 == 1 else "evidence")
            
            try:
                start_time = time.time()
                reply = dashboard_server.generate_chat_reply(
                    q, island_ctx, api_key, context_tab=tab_ctx
                )
                elapsed = time.time() - start_time

                title = reply.get("title", "")
                sections = reply.get("sections", [])
                links = reply.get("links", [])
                pose = reply.get("pose", "")

                # Basic validation checks
                has_title = bool(title and len(title) >= 3)
                has_sections = bool(sections and len(sections) >= 1)
                labels_ok = all(bool(s.get("label")) and bool(s.get("text")) for s in sections)
                
                # Check for vertical list formatting if top 10 or ranking asked
                list_formatted = True
                if "top 10" in q.lower() or "rank" in q.lower():
                    combined_text = "\n".join(s.get("text", "") for s in sections)
                    # Check if items are numbered with newlines or list items
                    has_numbered_items = "1." in combined_text and "2." in combined_text
                    if not has_numbered_items:
                        list_formatted = False

                is_ok = has_title and has_sections and labels_ok

                status_icon = "PASS" if is_ok else "WARN"
                if is_ok:
                    passed += 1

                print(f"[{total_tested:02d}] [{status_icon}] ({elapsed:.1f}s) Q: '{q}'")
                print(f"     Title: {title} | Pose: {pose} | Sections: {len(sections)} | Links: {len(links)}")
                if not list_formatted:
                    print("     [NOTE] Ranking query could be more explicitly numbered.")
                for s in sections[:2]:
                    preview = s.get('text', '').replace('\n', ' ')
                    if len(preview) > 95:
                        preview = preview[:92] + "..."
                    print(f"     * {s.get('label')}: {preview}")

            except Exception as err:
                print(f"[{total_tested:02d}] [FAIL] Q: '{q}' -> Error: {err}")

            time.sleep(delay_sec)

    print("\n" + "=" * 70)
    print(f"Completed Loop: {passed}/{total_tested} questions passed validation.")
    print("=" * 70)

if __name__ == "__main__":
    batches = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_loop(max_batches=batches, delay_sec=0.5)
