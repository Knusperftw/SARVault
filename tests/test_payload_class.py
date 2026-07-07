"""F3.1: payload_class dimension.

Guards that the checked-in dbt seed (dbt/seeds/target_payload_class.csv) stays in
sync with the single source of truth (config/target_set.yml), and that the extract
config exposes the mapping. If these drift, the marts layer would mislabel targets.
"""

import csv
from pathlib import Path

from extract.config import load_config
from scripts.gen_payload_class_seed import SEED_PATH, seed_rows

KNOWN_CLASSES = {"tubulin_inhibitor", "topo1_inhibitor", "topo2_inhibitor"}


def test_every_target_has_a_known_payload_class():
    config = load_config()
    for target in config.targets:
        assert target.payload_class in KNOWN_CLASSES, (
            f"{target.chembl_id} has payload_class {target.payload_class!r}"
        )


def test_payload_class_map_matches_targets():
    config = load_config()
    mapping = config.payload_class_map
    assert mapping == {t.chembl_id: t.payload_class for t in config.targets}


def test_seed_is_in_sync_with_config():
    config = load_config()
    expected = seed_rows(config)

    assert Path(SEED_PATH).exists(), "target_payload_class.csv seed is missing"
    with Path(SEED_PATH).open(newline="") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["target_chembl_id", "payload_class"]
    actual = [(r[0], r[1]) for r in rows[1:]]
    assert actual == expected, (
        "seed is out of sync with config; run: python -m scripts.gen_payload_class_seed"
    )
