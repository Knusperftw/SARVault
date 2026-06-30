"""Pandera schemas validating raw ChEMBL entities before they are landed.

The raw layer is intentionally permissive (most filtering happens in staging),
so these schemas assert structural essentials: the key identifier columns are
present and the provenance stamp is complete and non-null.
"""

from pandera.pandas import Column, DataFrameSchema

_PROVENANCE = {
    "_fetch_ts": Column(str, nullable=False),
    "_source_endpoint": Column(str, nullable=False),
    "_chembl_version": Column(str, nullable=False),
    "_row_hash": Column(str, nullable=False),
}


def _schema(columns: dict) -> DataFrameSchema:
    return DataFrameSchema({**columns, **_PROVENANCE}, coerce=True, strict=False)


ACTIVITIES_SCHEMA = _schema(
    {
        "molecule_chembl_id": Column(str, nullable=True),
        "target_chembl_id": Column(str, nullable=True),
        "assay_chembl_id": Column(str, nullable=True),
        "standard_type": Column(str, nullable=True),
        "pchembl_value": Column(float, nullable=True),
    }
)
MOLECULES_SCHEMA = _schema({"molecule_chembl_id": Column(str, nullable=True)})
TARGETS_SCHEMA = _schema({"target_chembl_id": Column(str, nullable=True)})
ASSAYS_SCHEMA = _schema({"assay_chembl_id": Column(str, nullable=True)})

SCHEMAS = {
    "activities": ACTIVITIES_SCHEMA,
    "molecules": MOLECULES_SCHEMA,
    "targets": TARGETS_SCHEMA,
    "assays": ASSAYS_SCHEMA,
}


def validate(entity: str, df):
    """Validate a raw entity DataFrame against its schema; returns the coerced df."""
    return SCHEMAS[entity].validate(df)
