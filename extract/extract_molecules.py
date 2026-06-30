"""Extract ChEMBL molecules referenced by the scoped activities."""

import requests

from extract.chembl_client import chunked, fetch_all

_CHUNK = 50  # small: ChEMBL rejects over-long __in URLs


def extract_molecules(molecule_ids, session: requests.Session | None = None) -> list[dict]:
    """Fetch molecule records for the given ChEMBL molecule IDs."""
    ids = sorted({mid for mid in molecule_ids if mid})
    records: list[dict] = []
    for chunk in chunked(ids, _CHUNK):
        params = {"molecule_chembl_id__in": ",".join(chunk)}
        records.extend(fetch_all("molecule", params, session=session))
    return records
