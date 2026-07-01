-- UniChem bulk cross-references (already scoped to our compounds by the extract).
select
    molecule_chembl_id,
    source,
    xref_id
from {{ source('raw', 'xref_unichem') }}
where molecule_chembl_id is not null
  and xref_id is not null
