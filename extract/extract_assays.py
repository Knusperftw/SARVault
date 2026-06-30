"""Extract ChEMBL assays referenced by the scoped activities."""

import requests

from extract.chembl_client import chunked, fetch_all

_CHUNK = 500


def extract_assays(assay_ids, session: requests.Session | None = None) -> list[dict]:
    """Fetch assay records for the given ChEMBL assay IDs."""
    ids = sorted({aid for aid in assay_ids if aid})
    records: list[dict] = []
    for chunk in chunked(ids, _CHUNK):
        params = {"assay_chembl_id__in": ",".join(chunk)}
        records.extend(fetch_all("assay", params, session=session))
    return records
