"""Generate the payload_class dbt seed from config/target_set.yml (the SSOT).

The seed (dbt/seeds/target_payload_class.csv) lets the marts layer join a
mechanism class onto every in-scope target. Config stays the single source of
truth: re-run this after editing the target set so the seed cannot drift.

    python -m scripts.gen_payload_class_seed

tests/test_payload_class.py fails if the checked-in seed is out of sync.
"""

import csv
from pathlib import Path

from extract.config import ExtractConfig, load_config

SEED_PATH = (
    Path(__file__).resolve().parents[1] / "dbt" / "seeds" / "target_payload_class.csv"
)
HEADER = ["target_chembl_id", "payload_class"]


def seed_rows(config: ExtractConfig) -> list[tuple[str, str]]:
    """Return sorted (target_chembl_id, payload_class) rows for the seed."""
    return sorted(
        (t.chembl_id, t.payload_class or "") for t in config.targets
    )


def generate(path: Path | str = SEED_PATH, config: ExtractConfig | None = None) -> Path:
    """Write the seed CSV from config and return its path."""
    config = config or load_config()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(seed_rows(config))
    return path


if __name__ == "__main__":
    out = generate()
    print(f"wrote {out}")
