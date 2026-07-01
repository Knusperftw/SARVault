"""Enrich compound cross-references from UniChem whole-source-mapping bulk dumps.

UniChem publishes per-source mapping files (src1src{id}.txt.gz) that map ChEMBL
IDs to a target source. We read only the sources we care about, filter each file
to the compounds already in raw/ (a semi-join in DuckDB, so we never load the
full multi-million-row file into memory), and land the result to raw/.

The live UniChem API proved unstable (500 / 503), so this uses the bulk dumps:
download the files once, then run this module before `dbt build`.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

# UniChem source name -> numeric sourceID (confirmed via /sources; ZINC is not
# among UniChem's current sources, so it is omitted).
SOURCES = {
    "pubchem": 22,
    "drugbank": 2,
    "pdbe": 5,
    "bindingdb": 31,
    "surechembl": 15,
}

DEFAULT_MAPPING_DIR = os.environ.get("UNICHEM_DIR", "data/unichem")
RAW_DIR = Path(__file__).resolve().parents[1] / "raw"
PROVENANCE_COLUMNS = ["_fetch_ts", "_source_endpoint", "_chembl_version", "_row_hash"]


def load_unichem_mappings(mapping_dir, chembl_ids, sources=None) -> pd.DataFrame:
    """Read the mapping dumps in ``mapping_dir`` and filter to ``chembl_ids``.

    Each file is a TSV whose first two columns are (chembl_id, target_id) with a
    header line; the inner join to our IDs drops the header and all out-of-scope
    compounds. Returns columns: molecule_chembl_id, source, xref_id.
    """
    sources = sources or SOURCES
    mapping_dir = Path(mapping_dir)
    con = duckdb.connect()
    con.register("ids", pd.DataFrame({"molecule_chembl_id": sorted(set(chembl_ids))}))
    frames = []
    for source, src_id in sources.items():
        path = mapping_dir / f"src1src{src_id}.txt.gz"
        if not path.exists():
            continue
        df = con.execute(
            """
            select m.column0 as molecule_chembl_id, ? as source, m.column1 as xref_id
            from read_csv(?, delim='\t', header=false, ignore_errors=true,
                         columns={'column0': 'VARCHAR', 'column1': 'VARCHAR'}) m
            join ids i on m.column0 = i.molecule_chembl_id
            """,
            [source, str(path)],
        ).df()
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["molecule_chembl_id", "source", "xref_id"])
    return pd.concat(frames, ignore_index=True)


def _row_hash(record: dict) -> str:
    encoded = json.dumps(record, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def land_unichem(df: pd.DataFrame, chembl_version: str, raw_dir=RAW_DIR) -> Path:
    """Stamp provenance and write raw_xref_unichem.parquet (empty df is fine)."""
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out["_fetch_ts"] = datetime.now(timezone.utc).isoformat()
    out["_source_endpoint"] = "unichem/wholeSourceMapping"
    out["_chembl_version"] = str(chembl_version)
    out["_row_hash"] = [_row_hash(r) for r in out.to_dict("records")]
    out_path = raw_dir / "raw_xref_unichem.parquet"
    out.to_parquet(out_path, index=False)
    return out_path


def main(mapping_dir: str = DEFAULT_MAPPING_DIR) -> None:
    from extract.config import load_config

    config = load_config()
    ids = (
        duckdb.connect()
        .execute("select distinct molecule_chembl_id from read_parquet('raw/raw_molecules.parquet')")
        .df()["molecule_chembl_id"]
        .tolist()
    )
    df = load_unichem_mappings(mapping_dir, ids)
    out = land_unichem(df, config.chembl_version)
    print(f"unichem xref: {len(df)} rows -> {out}")


if __name__ == "__main__":
    main()
