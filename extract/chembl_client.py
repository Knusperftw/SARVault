"""ChEMBL REST API client: a retrying requests session plus offset pagination.

The ChEMBL data API exposes collection endpoints (activity, molecule, target,
assay) as paginated JSON. This module provides a hardened session (retry +
backoff on transient errors) and a generator that walks every page of a
collection, so callers receive a flat stream of records.
"""

from collections.abc import Iterable, Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
PAGE_LIMIT = 1000
RETRY_STATUS = (429, 500, 502, 503, 504)


def build_session(total_retries: int = 5, backoff_factor: float = 0.5) -> requests.Session:
    """Return a requests session that retries transient HTTP errors with backoff."""
    retry = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=RETRY_STATUS,
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _collection_key(payload: dict) -> str:
    """Return the single record-list key in a ChEMBL response (e.g. 'activities')."""
    keys = [k for k in payload if k != "page_meta"]
    if not keys:
        raise ValueError("ChEMBL response contains no record collection")
    return keys[0]


def fetch_all(
    endpoint: str,
    params: dict,
    session: requests.Session | None = None,
    page_limit: int = PAGE_LIMIT,
    timeout: int = 60,
) -> Iterator[dict]:
    """Yield every record from a ChEMBL collection endpoint via offset pagination."""
    session = session or build_session()
    query = dict(params)
    query.setdefault("format", "json")
    query["limit"] = page_limit
    offset = 0
    collection_key = None
    while True:
        query["offset"] = offset
        response = session.get(f"{BASE_URL}/{endpoint}", params=query, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        if collection_key is None:
            collection_key = _collection_key(payload)
        yield from payload.get(collection_key, [])
        page_meta = payload.get("page_meta") or {}
        if not page_meta.get("next"):
            break
        offset += page_limit


def chunked(iterable: Iterable[str], size: int) -> Iterator[list[str]]:
    """Split an iterable into lists of at most ``size`` items."""
    items = list(iterable)
    for start in range(0, len(items), size):
        yield items[start : start + size]
