"""Extract ChEMBL activities for the configured target set.

Activities are the fact grain; the dimension IDs (molecule/target/assay) are
derived from the returned activity records by the runner.
"""

import requests

from extract.chembl_client import fetch_all
from extract.config import ExtractConfig, load_config


def build_activity_params(config: ExtractConfig) -> dict:
    """Build the ChEMBL /activity query parameters from the config."""
    params = {
        "target_chembl_id__in": ",".join(config.target_ids),
        "standard_type__in": ",".join(config.activity.standard_types),
    }
    if config.activity.require_pchembl:
        params["pchembl_value__isnull"] = "false"
    return params


def extract_activities(
    config: ExtractConfig | None = None,
    session: requests.Session | None = None,
) -> list[dict]:
    """Fetch all activity records for the configured scope."""
    config = config or load_config()
    return list(fetch_all("activity", build_activity_params(config), session=session))
