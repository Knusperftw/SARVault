"""Extract ChEMBL targets referenced by the scoped activities."""

import requests

from extract.chembl_client import chunked, fetch_all

_CHUNK = 500


def extract_targets(target_ids, session: requests.Session | None = None) -> list[dict]:
    """Fetch target records for the given ChEMBL target IDs."""
    ids = sorted({tid for tid in target_ids if tid})
    records: list[dict] = []
    for chunk in chunked(ids, _CHUNK):
        params = {"target_chembl_id__in": ",".join(chunk)}
        records.extend(fetch_all("target", params, session=session))
    return records
