"""Load the published 2011-2015 Malaysian Marine Parks TEV benchmark."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = (
    ROOT
    / "data/raw/structured/economic_valuation/dmpm_tev_2011_2015.csv"
)
SOURCE_URL = (
    "https://wdpa.s3.amazonaws.com/Country_informations/MYS/"
    "TOTAL%20ECONOMIC%20VALUE%20OF%20MARINE%20BIODIVERSITY.pdf"
)
CALCULATED_TOTAL_MYR = 8_686_990_000
REPORTED_TOTAL_MYR = 8_700_000_000


def load_dmpm_tev(path=DATA_PATH):
    """Return the source-transcribed TEV benchmark and validate its total."""
    with Path(path).open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

    components = [
        {
            "component": row["component"],
            "annual_value_myr": int(row["annual_value_myr"]),
            "source_page": int(row["source_page"]),
        }
        for row in rows
    ]
    calculated_total = sum(row["annual_value_myr"] for row in components)
    if calculated_total != CALCULATED_TOTAL_MYR:
        raise ValueError(
            f"DMPM TEV components total {calculated_total}, expected "
            f"{CALCULATED_TOTAL_MYR}"
        )

    return {
        "publication": "Total Economic Value of Marine Biodiversity: Malaysia Marine Parks",
        "publisher": "Department of Marine Park Malaysia",
        "study_period": "2011-2015",
        "evaluated_archipelagos": 6,
        "scope_note": (
            "Published annual benchmark for six evaluated Malaysian marine-park "
            "archipelagos; not a current ReefSafe estimate"
        ),
        "reported_total_myr": REPORTED_TOTAL_MYR,
        "calculated_total_myr": calculated_total,
        "source_url": SOURCE_URL,
        "components": components,
    }


if __name__ == "__main__":
    valuation = load_dmpm_tev()
    print(f"Published headline: RM {valuation['reported_total_myr'] / 1e9:.1f} billion/year")
