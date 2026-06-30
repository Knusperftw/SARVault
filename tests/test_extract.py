"""M1: unit tests for the extract layer (no live API calls)."""

import pandas as pd
import pytest

from extract import load_raw as load_raw_mod
from extract.chembl_client import chunked, fetch_all
from extract.config import load_config
from extract.extract_activities import build_activity_params
from extract.load_raw import load_raw, row_hash
from validation.schemas import validate


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSession:
    """Returns queued pages in order, recording the offsets requested."""

    def __init__(self, pages):
        self._pages = list(pages)
        self.offsets = []
        self.calls = 0

    def get(self, url, params=None, timeout=None):
        self.offsets.append(params.get("offset"))
        page = self._pages[self.calls]
        self.calls += 1
        return _FakeResponse(page)


def test_fetch_all_paginates_until_next_is_null():
    pages = [
        {"activities": [{"id": 1}, {"id": 2}], "page_meta": {"next": "/x?offset=2"}},
        {"activities": [{"id": 3}], "page_meta": {"next": None}},
    ]
    session = _FakeSession(pages)
    records = list(fetch_all("activity", {}, session=session, page_limit=2))
    assert [r["id"] for r in records] == [1, 2, 3]
    assert session.offsets == [0, 2]


def test_chunked_splits_evenly():
    assert list(chunked(["a", "b", "c", "d", "e"], 2)) == [["a", "b"], ["c", "d"], ["e"]]


def test_config_has_four_verified_targets():
    config = load_config()
    assert config.target_ids == [
        "CHEMBL2095182",
        "CHEMBL3832942",
        "CHEMBL1781",
        "CHEMBL1806",
    ]


def test_build_activity_params_encodes_filters():
    params = build_activity_params(load_config())
    assert "CHEMBL1781" in params["target_chembl_id__in"]
    assert "IC50" in params["standard_type__in"]
    assert params["pchembl_value__isnull"] == "false"


def test_row_hash_is_stable_and_order_independent():
    assert row_hash({"x": 1, "y": 2}) == row_hash({"y": 2, "x": 1})


def test_load_raw_writes_parquet_with_provenance(tmp_path):
    records = [
        {"molecule_chembl_id": "CHEMBL1", "synonyms": ["foo", "bar"]},
        {"molecule_chembl_id": "CHEMBL2", "synonyms": []},
    ]
    out = load_raw("molecules", records, "36", endpoint="molecule", raw_dir=tmp_path)
    df = pd.read_parquet(out)
    assert len(df) == 2
    for col in load_raw_mod.PROVENANCE_COLUMNS:
        assert col in df.columns
        assert df[col].notna().all()
    assert (df["_source_endpoint"] == "molecule").all()
    assert (df["_chembl_version"] == "36").all()
    assert isinstance(df["synonyms"].iloc[0], str)  # nested list serialized to JSON


def test_pandera_schema_rejects_missing_provenance():
    valid = pd.DataFrame(
        {
            "molecule_chembl_id": ["CHEMBL1"],
            "_fetch_ts": ["2026-01-01T00:00:00+00:00"],
            "_source_endpoint": ["molecule"],
            "_chembl_version": ["36"],
            "_row_hash": ["abc"],
        }
    )
    validate("molecules", valid)  # should not raise
    with pytest.raises(Exception):
        validate("molecules", valid.drop(columns=["_row_hash"]))
