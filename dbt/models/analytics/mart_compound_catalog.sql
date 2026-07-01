-- Compound catalog (grain: compound). One row per measured compound with
-- identity, structure, physicochemical properties and potency summary.
with selectivity as (
    select * from {{ ref('mart_compound_selectivity') }}
),
compound as (
    select * from {{ ref('dim_compound') }}
)

select
    s.compound_key,
    c.molecule_chembl_id,
    c.pref_name,
    c.canonical_smiles,
    c.inchi_key,
    c.mw_freebase,
    c.alogp,
    c.hba,
    c.hbd,
    c.psa,
    c.rotatable_bonds,
    c.num_ro5_violations,
    c.ro3_pass,
    c.aromatic_rings,
    c.qed_weighted,
    c.max_phase,
    c.is_approved_drug,
    c.molecule_type,
    s.n_targets,
    s.best_pchembl,
    s.best_target,
    s.selectivity_index
from selectivity s
join compound c on s.compound_key = c.compound_key
