-- Chemical-series mart (grain: scaffold). One row per Bemis-Murcko scaffold with
-- the size, potency spread and target reach of the compounds that share it — the
-- unit a medicinal chemist reasons about (a chemical series), rather than isolated
-- compounds. Acyclic compounds have no scaffold and are not part of any series.
--
-- Potency is summarised per compound as its best (max median) pChEMBL across the
-- targets it was measured on, taken from mart_target_sar (so this model does not
-- depend on the enrichment marts).
with members as (
    select scaffold_key, compound_key, molecule_chembl_id
    from {{ ref('mart_compound_fingerprint') }}
    where scaffold_key is not null
),

compound_potency as (
    select
        compound_key,
        max(median_pchembl)         as best_pchembl,
        count(distinct target_key)  as n_targets
    from {{ ref('mart_target_sar') }}
    group by compound_key
),

series_targets as (
    select m.scaffold_key, count(distinct s.target_key) as n_targets
    from members m
    join {{ ref('mart_target_sar') }} s on m.compound_key = s.compound_key
    group by m.scaffold_key
),

agg as (
    select
        m.scaffold_key,
        count(distinct m.compound_key)                       as n_compounds,
        count(distinct case when p.best_pchembl is not null
                            then m.compound_key end)         as n_measured_compounds,
        median(p.best_pchembl)                               as median_pchembl,
        max(p.best_pchembl)                                  as max_pchembl,
        min(p.best_pchembl)                                  as min_pchembl,
        arg_max(m.molecule_chembl_id, p.best_pchembl)        as top_compound
    from members m
    left join compound_potency p on m.compound_key = p.compound_key
    group by m.scaffold_key
)

select
    d.scaffold_key,
    d.murcko_scaffold_smiles,
    d.murcko_generic_smiles,
    a.n_compounds,
    a.n_measured_compounds,
    coalesce(st.n_targets, 0)                        as n_targets,
    round(a.median_pchembl, 2)                       as median_pchembl,
    round(a.max_pchembl, 2)                          as max_pchembl,
    round(a.min_pchembl, 2)                          as min_pchembl,
    round(a.max_pchembl - a.min_pchembl, 2)          as pchembl_range,
    a.top_compound
from {{ ref('dim_scaffold') }} d
join agg a on d.scaffold_key = a.scaffold_key
left join series_targets st on d.scaffold_key = st.scaffold_key
