"""Pure DataFrame helpers for scope filtering and landing-page metrics."""


def _target_keys(target_sar, targets):
    if not targets:
        return set(target_sar["compound_key"])
    return set(target_sar.loc[target_sar["target_pref_name"].isin(targets), "compound_key"])


def resolve_scope_keys(target_sar, catalog, scope):
    """Compound keys passing the scope's target / approval / min-potency facets."""
    scope = scope or {}
    keys = _target_keys(target_sar, scope.get("targets"))
    cat = catalog[catalog["compound_key"].isin(keys)]
    approval = scope.get("approval", "all")
    if approval == "approved":
        cat = cat[cat["is_approved_drug"]]
    elif approval == "research":
        cat = cat[~cat["is_approved_drug"]]
    min_p = scope.get("min_pchembl") or 0
    if min_p > 0:
        cat = cat[cat["best_pchembl"].fillna(-1) >= min_p]
    return set(cat["compound_key"])


def scoped_target_sar(target_sar, scope, keys):
    """SAR pairs limited to in-scope compounds and (if set) selected targets."""
    scope = scope or {}
    df = target_sar[target_sar["compound_key"].isin(keys)]
    targets = scope.get("targets")
    if targets:
        df = df[df["target_pref_name"].isin(targets)]
    return df


def overview_metrics(target_sar, catalog, scope):
    """Headline metrics for the landing page, restricted to the current scope."""
    keys = resolve_scope_keys(target_sar, catalog, scope)
    sar = scoped_target_sar(target_sar, scope, keys)
    cat = catalog[catalog["compound_key"].isin(keys)]
    return {
        "compounds": int(len(keys)),
        "activities": int(sar["n_measurements"].sum()),
        "targets": int(sar["target_pref_name"].nunique()),
        "pairs": int(len(sar)),
        "multi_target": int((cat["n_targets"] >= 2).sum()),
        "approved": int(cat["is_approved_drug"].sum()),
    }
