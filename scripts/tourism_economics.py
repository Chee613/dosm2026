"""Park-level reef-attributable tourism spending, a national estimate, and the season rest.

Visitors come from two official sources only: the Department of Marine Park state
series (2013-2017 average, peninsular parks and Labuan) and Sabah Parks (2024).
Units outside those parks - Malacca and non-park reefs - are excluded rather than
estimated. The accommodation inventory is never used. Nothing here is a forecast;
every figure is arithmetic on published inputs.
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
DMPM_YEARS = range(2013, 2018)     # Department of Marine Park series ends in 2017

SPEND_PER_VISITOR_RM = DTS_RECEIPTS_RM / DTS_VISITORS

DMPM_SOURCE = ("Department of Marine Park Malaysia / data.gov.my",
               "https://archive.data.gov.my/data/en_US/organization/department-of-marine-park-malaysia")

# Each park, where its visitors come from, and which monitoring units (by the
# marine_park label in the ranking) it contains.
DMPM_PARKS = [
    ("Mersing Marine Parks", "Johor", ["Mersing Marine Park"]),
    ("Pulau Payar Marine Park", "Kedah", ["Pulau Payar Marine Park"]),
    ("Tioman Marine Parks", "Pahang", ["Tioman Marine Park", "Tioman Marine Park Buffer"]),
    ("Terengganu Marine Parks", "Terengganu", ["Terengganu Marine Park"]),
    ("Labuan Marine Park", "Labuan", ["Labuan Marine Park"]),
]
SABAH_PARKS = [
    # (row in island_arrivals.csv, park name, marine_park labels it contains)
    ("Tunku Abdul Rahman Park", "Tunku Abdul Rahman Park", ["Tunku Abdul Rahman Park"]),
    ("Tun Sakaran Marine Park", "Tun Sakaran Marine Park", ["Tun Sakaran Marine Park"]),
    ("Sipadan", "Sipadan Island Park", ["Sipadan Island Park"]),
    ("Penyu", "Turtle Islands Park", ["Turtle Islands National Park"]),
    ("Tiga", "Pulau Tiga Park", ["Pulau Tiga National Park"]),
]

SOURCES = {
    "spend": "DOSM Domestic Tourism Survey 2024: RM106.7bn / 260.1m domestic visitors "
             f"= RM{SPEND_PER_VISITOR_RM:.0f} per visitor, applied to all visitors, so spending is a floor.",
    "reef_adjacent": "Reef-adjacent share: 10% of tourism spending (Spalding et al. 2017), a foreign "
                     "method coefficient applied to Malaysian inputs only.",
    "visitors": "Visitors: Department of Marine Park state series, 2013-2017 average (data.gov.my); "
                "Sabah Parks public visitor statistics, 2024.",
    "recovery": "Reef recovery needs at least 10-15 years without new disturbance (James Cook University, 2019).",
}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def park_records(priority):
    units_by_park = {}
    for row in priority:
        units_by_park.setdefault(row["marine_park"], []).append(row)

    dmpm = read_csv(RAW / "taman_laut_visitors_2000_2017.csv")
    arrivals = {row["island"]: row for row in read_csv(RAW / "tourism" / "island_arrivals.csv")}

    parks = []
    for name, state, labels in DMPM_PARKS:
        # A zero total means the year was not recorded (Labuan shows 0 for 2013-2015),
        # so average only the years with records.
        recorded = {int(row["year"]): int(row["total_visitors"]) for row in dmpm
                    if row["state"] == state and int(row["year"]) in DMPM_YEARS and int(row["total_visitors"]) > 0}
        years = sorted(recorded)
        parks.append((name, state, labels, sum(recorded.values()) / len(recorded),
                      f"{years[0]}-{years[-1]} average", *DMPM_SOURCE))
    for arrival_row, name, labels in SABAH_PARKS:
        row = arrivals[arrival_row]
        parks.append((name, "Sabah", labels, float(row["arrivals_total"]),
                      f"{row['year']} full year", row["source_name"], row["source_url"]))

    records = []
    for name, state, labels, visitors, basis, source_name, source_url in parks:
        units = [unit for label in labels for unit in units_by_park.get(label, [])]
        spending = visitors * SPEND_PER_VISITOR_RM
        records.append({
            "park": name,
            "state": state,
            "visitors_per_year": round(visitors),
            "spending_rm": round(spending),
            "reef_adjacent_rm": round(spending * REEF_ADJACENT_SHARE),
            "basis": basis,
            "units": "; ".join(sorted(unit["island"] for unit in units)),
            "high_priority_units": "; ".join(sorted(unit["island"] for unit in units if "High" in unit["priority_tier"])),
            "source_name": source_name,
            "source_url": source_url,
        })
    return sorted(records, key=lambda record: -record["reef_adjacent_rm"])


def season_tradeoff(records, priority):
    """One month of rest across the parks that contain high-priority units, against the
    reef-attributable revenue those parks earn across a recovery window."""
    high_units = [row["island"] for row in priority if "High" in row["priority_tier"]]
    parks = [row for row in records if row["high_priority_units"]]
    covered = sorted(unit for row in parks for unit in row["high_priority_units"].split("; "))
    monthly_loss = sum(row["spending_rm"] for row in parks) * CLOSURE_MONTHS / 12.0
    annual_reef_value = sum(row["reef_adjacent_rm"] for row in parks)
    low_years, high_years = RECOVERY_YEARS
    return {
        "closure_months": CLOSURE_MONTHS,
        "park_names": [row["park"] for row in parks],
        "units_total": len(high_units),
        "units_covered": len(covered),
        "units_covered_names": covered,
        "units_uncovered_names": sorted(set(high_units) - set(covered)),
        "short_term_loss_rm": round(monthly_loss),
        "reef_adjacent_annual_rm": annual_reef_value,
        "long_term_low_rm": annual_reef_value * low_years,
        "long_term_high_rm": annual_reef_value * high_years,
        "recovery_years": list(RECOVERY_YEARS),
        "recovery_mid_years": (low_years + high_years) / 2,
        "long_term_mid_rm": round(annual_reef_value * (low_years + high_years) / 2),
        # Both sides scale with the same spending, so their ratio is fixed by the
        # assumptions (share x 12 months x years) and must not be shown as a finding.
        "ratio_note": f"The ratio between the two figures is {REEF_ADJACENT_SHARE * 12 * low_years:.0f}-"
                      f"{REEF_ADJACENT_SHARE * 12 * high_years:.0f}x by construction (10% share x 12 months "
                      f"x {low_years}-{high_years} years); published visitors set only the scale.",
    }


def main():
    priority = read_csv(PROCESSED / "reef_priority_predictions.csv")
    records = park_records(priority)

    with open(PROCESSED / "park_economics.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    covered_units = {unit for row in records for unit in row["units"].split("; ") if unit}
    payload = {
        "parks": len(records),
        "units_total": len(priority),
        "units_covered": len(covered_units),
        "units_excluded": sorted(row["island"] for row in priority if row["island"] not in covered_units),
        "national_visitors": sum(row["visitors_per_year"] for row in records),
        "national_spending_rm": sum(row["spending_rm"] for row in records),
        "national_reef_adjacent_rm": sum(row["reef_adjacent_rm"] for row in records),
        "spend_per_visitor_rm": round(SPEND_PER_VISITOR_RM),
        "reef_adjacent_share": REEF_ADJACENT_SHARE,
        "tradeoff": season_tradeoff(records, priority),
        "sources": SOURCES,
    }
    (PROCESSED / "tourism_economics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    tradeoff = payload["tradeoff"]
    print(f"National estimate: {payload['parks']} parks, {payload['national_visitors']:,} visitors/yr, "
          f"reef-adjacent RM{payload['national_reef_adjacent_rm'] / 1e6:.1f}M/yr")
    print(f"Units covered: {payload['units_covered']} of {payload['units_total']}; excluded: {', '.join(payload['units_excluded'])}")
    print(f"Season rest across {len(tradeoff['park_names'])} parks ({tradeoff['units_covered']}/{tradeoff['units_total']} "
          f"high-priority units): RM{tradeoff['short_term_loss_rm'] / 1e6:.1f}M against "
          f"RM{tradeoff['long_term_low_rm'] / 1e6:.0f}-{tradeoff['long_term_high_rm'] / 1e6:.0f}M")


if __name__ == "__main__":
    main()
