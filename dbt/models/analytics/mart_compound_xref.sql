-- Compound cross-references (grain: compound x source x xref_id) with resolved URLs.
-- Combines ChEMBL's own molecule cross_references (stage 1) with UniChem bulk
-- cross-references (stage 2), keyed to dim_compound and linked via the seed.
with chembl_xref as (
    select molecule_chembl_id, source, xref_id from {{ ref('stg_compound_xref') }}
),
unichem_xref as (
    select molecule_chembl_id, source, xref_id from {{ ref('stg_compound_xref_unichem') }}
),
combined as (
    select * from chembl_xref
    union all
    select * from unichem_xref
),
compound as (
    select compound_key, molecule_chembl_id from {{ ref('dim_compound') }}
),
sources as (
    select * from {{ ref('xref_sources') }}
)

select distinct
    c.compound_key,
    x.molecule_chembl_id,
    x.source,
    coalesce(s.display_name, upper(substr(x.source, 1, 1)) || substr(x.source, 2)) as display_name,
    x.xref_id,
    case
        when s.url_template is not null
        then replace(s.url_template, '{id}', x.xref_id)
    end as url
from combined x
join compound c on x.molecule_chembl_id = c.molecule_chembl_id
left join sources s on x.source = s.source
