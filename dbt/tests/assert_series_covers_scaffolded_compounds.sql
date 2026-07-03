-- The series mart must account for every compound that has a scaffold, exactly once:
-- sum of per-series member counts == number of distinct compounds with a scaffold_key.
with series_total as (
    select coalesce(sum(n_compounds), 0) as n from {{ ref('mart_chemical_series') }}
),
scaffolded as (
    select count(distinct compound_key) as n
    from {{ ref('mart_compound_fingerprint') }}
    where scaffold_key is not null
)
select series_total.n as series_n, scaffolded.n as scaffolded_n
from series_total, scaffolded
where series_total.n <> scaffolded.n
