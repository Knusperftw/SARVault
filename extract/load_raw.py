"""Land fetched ChEMBL records to the raw layer as Parquet with provenance.

Every row is stamped with _fetch_ts, _source_endpoint, _chembl_version and a
_row_hash of the source record, so downstream layers can trace lineage. Records
are validated against their Pandera schema before being written.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[1] / "raw"
PROVENANCE_COLUMNS = ["_fetch_ts", "_source_endpoint", "_chembl_version", "_row_hash"]


def row_hash(record: dict) -> str:
    """Return a stable SHA-256 hash of a source record (key-order independent)."""
    encoded = json.dumps(record, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _stringify_nested(df: pd.DataFrame) -> pd.DataFrame:
    """Serialize list/dict cells to JSON strings so Parquet can store them."""
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, (list, dict))).any():
            df[col] = df[col].map(
                lambda v: json.dumps(v, default=str) if isinstance(v, (list, dict)) else v
            )
    return df


def add_provenance(
    df: pd.DataFrame, records: list[dict], endpoint: str, chembl_version: str
) -> pd.DataFrame:
    """Attach provenance columns to a normalized DataFrame."""
    df = df.copy()
    df["_fetch_ts"] = datetime.now(timezone.utc).isoformat()
    df["_source_endpoint"] = endpoint
    df["_chembl_version"] = str(chembl_version)
    df["_row_hash"] = [row_hash(r) for r in records]
    return df


def load_raw(
    entity: str,
    records: list[dict],
    chembl_version: str,
    endpoint: str | None = None,
    raw_dir: Path | str = RAW_DIR,
    validate_schema: bool = True,
) -> Path:
    """Normalize, stamp, validate and write an entity to raw_<entity>.parquet."""
    endpoint = endpoint or entity
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    df = pd.json_normalize(records)
    df = add_provenance(df, records, endpoint, chembl_version)
    if validate_schema:
        from validation.schemas import validate

        df = validate(entity, df)
    df = _stringify_nested(df)
    out_path = raw_dir / f"raw_{entity}.parquet"
    df.to_parquet(out_path, index=False)
    return out_path
