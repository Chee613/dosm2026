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

JUDGING_QUESTIONS = [
    # --- Rubric Category 1: Model Selection & Hyperparameter Optimization ---
    ("Model Selection", "Why did you choose a Gradient Boosting Regressor over Random Forest or Ridge regression, and what are the exact hyperparameters?"),
    ("Model Selection", "What is the training sample size and how many transition records were used to fit the ensemble?"),
    ("Model Selection", "How does your model's MAE of 5.862 pp/yr compare to the naive historical baseline?"),
    ("Model Selection", "Why did Random Forest perform worse than Gradient Boosting on your forward test?"),

    # --- Rubric Category 2: Validation Methodology & Data Leakage ---
    ("Validation Rigor", "How did you structure the cross-validation to prevent temporal data leakage?"),
    ("Validation Rigor", "Explain how fold-local median imputation works and why global imputation would invalidate results."),
    ("Validation Rigor", "What are the validation MAE and bias metrics across target years 2021 to 2025?"),
    ("Validation Rigor", "Why does the year 2022 exhibit a higher MAE (6.959 pp/yr) compared to other years?"),
    ("Validation Rigor", "How is the 95% pooled forward-test residual distribution of [-16.25, +13.66 pp/yr] computed?"),

    # --- Rubric Category 3: Feature Engineering & Attribution ---
    ("Feature Engineering", "What are the 22 features used in the model and how are they grouped into factor categories?"),
    ("Feature Engineering", "According to permutation importance, which feature provides the strongest predictive signal?"),
    ("Feature Engineering", "Why do several lower-ranked features exhibit negative permutation importance?"),
    ("Feature Engineering", "Explain the mathematics of Tree-Path Decomposition (Saabas 2014) in deriving unit-level stress contributions."),
    ("Feature Engineering", "What is the base prediction value across all units, and how do factor contributions sum to the final output?"),
    ("Feature Engineering", "Why is NOAA Degree Heating Weeks (DHW) excluded from the scored model features?"),

    # --- Rubric Category 4: Uncertainty & Interpretation Boundaries ---
    ("Analytical Rigor", "Is this model causal or correlational, and how do you prevent users from over-interpreting predictions?"),
    ("Analytical Rigor", "How does ReefSafe communicate prediction uncertainty to non-technical marine park managers?"),
    ("Analytical Rigor", "Why can't this model determine the exact percentage of coral loss caused by tourism?"),

    # --- Rubric Category 5: Data Integration & Provenance ---
    ("Data Integration", "How do you reconcile the differing spatial resolutions between 100m transects, state GDP, and 5km satellite pixels?"),
    ("Data Integration", "What official datasets from data.gov.my and OpenDOSM were integrated into the diagnostic framework?"),
    ("Data Integration", "What role does JUPEM and DOFM play in the data pipeline?"),
    ("Data Integration", "Why was the static 56-island accommodation inventory excluded from the platform?"),

    # --- Rubric Category 6: Socio-Economic Attribution vs Valuation ---
    ("Economic Methodology", "Critique your reef-adjacent economy formula: why is a 10% global coefficient appropriate for Malaysia?"),
    ("Economic Methodology", "What is the distinction between the RM60.09M annual spending proxy and the RM8.7B TEV study by DMPM?"),
    ("Economic Methodology", "How is the RM410 average expenditure per visitor justified using official DOSM publications?"),
    ("Economic Methodology", "How many monitoring units are covered by the 4 marine parks in the economic calculation?"),

    # --- Rubric Category 7: Real-World Implementation & Field Impact ---
    ("Real-World Impact", "How does a marine park ranger operationalize the top 25% screening priority queue?"),
    ("Real-World Impact", "Walk me through the exact field verification protocol when Labuan or Kapas is flagged for urgent survey."),
    ("Real-World Impact", "How does ReefSafe align with SDG 14 (Life Below Water) and national marine conservation policies?"),

    # --- Rubric Category 8: Commercial Scalability & Innovation ---
    ("Scalability & Innovation", "What is the commercialization path for ReefSafe without compromising open public evidence?"),
    ("Scalability & Innovation", "What represents the core technological innovation of ReefSafe compared to static PDF survey reports?"),
]

LOG_FILE = "judging_chat_eval.log"

def main():
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Datathon Judging Continuous Evaluation Loop...")
    print(f"Loaded {len(JUDGING_QUESTIONS)} specialized technical judging questions.")
    print(f"Streaming evaluation logs to: {os.path.abspath(LOG_FILE)}\n")
    sys.stdout.flush()

    iteration = 0
    consecutive_429 = 0

    while True:
        iteration += 1
        category, q_text = random.choice(JUDGING_QUESTIONS)
        island = random.choice(["Labuan", "Redang", "Tioman", "Kapas", "Perhentian", "Tinggi", "Kapalai"])
        tab = random.choice(["overview", "diagnostics", "evidence"])

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = [f"\n=== [Judge Iter {iteration:04d}] {timestamp} | Rubric Focus: {category} ==="]
        log_entry.append(f"Judge Question: \"{q_text}\"")
        log_entry.append(f"Context: Island={island}, Tab={tab}")

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

            log_entry.append(f"Model Defense ({elapsed:.2f}s) | Title: {title} | Pose: {pose} | Links: {len(links)}")
            for sec in sections:
                label = sec.get("label", "INFO")
                text = sec.get("text", "")
                log_entry.append(f"  [{label}]:\n    {text}")
            if links:
                log_entry.append(f"  [CITATIONS]: {', '.join(links)}")

            status_str = f"[{timestamp}] Judge Iter {iteration:04d} [{category}]: SUCCESS ({elapsed:.1f}s) -> '{title}'"
            print(status_str)
            sys.stdout.flush()

        except urllib.error.HTTPError as err:
            elapsed = time.time() - t0
            if err.code == 429:
                consecutive_429 += 1
                backoff = min(60, 6 * consecutive_429)
                msg = f"[{timestamp}] Judge Iter {iteration:04d}: RATE LIMITED (HTTP 429). Backing off {backoff}s..."
                print(msg)
                log_entry.append(f"ERROR: {msg}")
                sys.stdout.flush()
                time.sleep(backoff)
            else:
                msg = f"[{timestamp}] Judge Iter {iteration:04d}: HTTP ERROR {err.code}: {err.reason}"
                print(msg)
                log_entry.append(f"ERROR: {msg}")
                sys.stdout.flush()

        except Exception as ex:
            elapsed = time.time() - t0
            msg = f"[{timestamp}] Judge Iter {iteration:04d}: EXCEPTION: {ex}"
            print(msg)
            log_entry.append(f"ERROR: {msg}")
            sys.stdout.flush()

        # Append to log
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as lf:
                lf.write("\n".join(log_entry) + "\n")
        except Exception:
            pass

        time.sleep(3.5)  # Respect API quota rate limits

if __name__ == "__main__":
    main()
