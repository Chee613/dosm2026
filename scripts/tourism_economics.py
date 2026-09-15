"""Reef-attributable tourism spending and the season-rest comparison.

Uses only islands with published arrivals (Sabah Parks, Terengganu state tourism).
No island is estimated from room counts: the accommodation inventory is excluded
from every claim in this repository. Nothing here is a forecast; the figures are
arithmetic on published inputs, each carried with the source shown beside it.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "structured"
PROCESSED = ROOT / "data" / "processed"

# Published inputs and the sources that must be shown next to them.
DTS_RECEIPTS_RM = 106.7e9          # DOSM Domestic Tourism Survey 2024
DTS_VISITORS = 260.1e6             # DOSM Domestic Tourism Survey 2024
REEF_ADJACENT_SHARE = 0.10         # Spalding et al. 2017, Marine Policy 82:104-113
RECOVERY_YEARS = (10, 15)          # James Cook University (2019): at least 10-15 years undisturbed
CLOSURE_MONTHS = 1

SPEND_PER_VISITOR_RM = DTS_RECEIPTS_RM / DTS_VISITORS

SOURCES = {
    "spend": "DOSM Domestic Tourism Survey 2024: RM106.7bn / 260.1m domestic visitors "
             f"= RM{SPEND_PER_VISITOR_RM:.0f} per visitor, applied to all visitors, so island "
             "spending is a floor. DMPM's marine-park estimate of RM450 per visitor is a cross-check.",
    "reef_adjacent": "Reef-adjacent share: 10% of island tourism spending (Spalding et al. 2017, "
                     "Marine Policy 82:104-113). A foreign method coefficient used as supporting "
                     "context only; every input it multiplies is Malaysian.",
    "arrivals": "Arrivals: Sabah Parks public visitor statistics (full year 2024) and the "
                "Terengganu State Tourism Department (January-August 2024, annualised).",
    "recovery": "Reef recovery needs at least 10-15 years without new disturbance "
                "(James Cook University, 2019).",
}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def island_economics(priority, arrivals):
    """One record per island that has published arrivals and a current screening rank."""
    ranked = {row["island"]: row for row in priority}
    records = []
    for row in arrivals:
        island = row["island"]
        if island not in ranked:
            continue
        reported = float(row["arrivals_total"])
        months = float(row["period_months"])
        visitors = reported * 12.0 / months
        window = "full year" if months == 12 else "Jan-Aug"
        basis = f"{reported:,.0f} visitors reported for {window} {row['year']}"
        if months != 12:
            basis += f", annualised to {visitors:,.0f}"
        spending = visitors * SPEND_PER_VISITOR_RM
        records.append({
            "island": island,
            "state": ranked[island]["state"],
            "priority_rank": int(ranked[island]["priority_rank"]),
            "priority_tier": ranked[island]["priority_tier"],
            "visitors_per_year": round(visitors),
            "spending_rm": round(spending),
            "reef_adjacent_rm": round(spending * REEF_ADJACENT_SHARE),
            "basis": basis,
            "source_name": row["source_name"],
            "source_url": row["source_url"],
        })
    return sorted(records, key=lambda record: -record["reef_adjacent_rm"])


def season_tradeoff(records, priority):
    """One month of rest on the high-priority islands with published arrivals, against the
    reef-attributable revenue those same islands earn across a recovery window."""
    high_total = sum(1 for row in priority if "High" in row["priority_tier"])
    measured = [row for row in records if "High" in row["priority_tier"]]
    monthly_loss = sum(row["spending_rm"] for row in measured) * CLOSURE_MONTHS / 12.0
    annual_reef_value = sum(row["reef_adjacent_rm"] for row in measured)
    low_years, high_years = RECOVERY_YEARS
    return {
        "closure_months": CLOSURE_MONTHS,
        "islands_total": high_total,
        "islands_measured": len(measured),
        "island_names": [row["island"] for row in measured],
        "short_term_loss_rm": round(monthly_loss),
        "reef_adjacent_annual_rm": annual_reef_value,
        "long_term_low_rm": annual_reef_value * low_years,
        "long_term_high_rm": annual_reef_value * high_years,
        "recovery_years": list(RECOVERY_YEARS),
        # Both sides scale with the same spending, so their ratio is fixed by the
        # assumptions (share x 12 months x years) and must not be shown as a finding.
        "ratio_note": f"The ratio between the two figures is {REEF_ADJACENT_SHARE * 12 * low_years:.0f}-"
                      f"{REEF_ADJACENT_SHARE * 12 * high_years:.0f}x by construction (10% share x 12 months "
                      f"x {low_years}-{high_years} years); published arrivals set only the scale.",
    }


def main():
    priority = read_csv(PROCESSED / "reef_priority_predictions.csv")
    arrivals = read_csv(RAW / "tourism" / "island_arrivals.csv")
    records = island_economics(priority, arrivals)

    with open(PROCESSED / "island_economics.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    payload = {
        "islands_measured": len(records),
        "islands_total": len(priority),
        "measured_visitors": sum(row["visitors_per_year"] for row in records),
        "measured_spending_rm": sum(row["spending_rm"] for row in records),
        "measured_reef_adjacent_rm": sum(row["reef_adjacent_rm"] for row in records),
        "spend_per_visitor_rm": round(SPEND_PER_VISITOR_RM),
        "reef_adjacent_share": REEF_ADJACENT_SHARE,
        "tradeoff": season_tradeoff(records, priority),
        "sources": SOURCES,
    }
    (PROCESSED / "tourism_economics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    tradeoff = payload["tradeoff"]
    print(f"Islands with published arrivals: {len(records)} of {len(priority)} ranked")
    print(f"Reef-attributable spending: RM{payload['measured_reef_adjacent_rm'] / 1e6:.1f}M/year")
    if tradeoff["short_term_loss_rm"]:
        print(f"One-month rest on {tradeoff['islands_measured']}/{tradeoff['islands_total']} high-priority islands: "
              f"RM{tradeoff['short_term_loss_rm'] / 1e6:.2f}M against "
              f"RM{tradeoff['long_term_low_rm'] / 1e6:.1f}-{tradeoff['long_term_high_rm'] / 1e6:.1f}M "
              f"over {RECOVERY_YEARS[0]}-{RECOVERY_YEARS[1]} years")


if __name__ == "__main__":
    main()
