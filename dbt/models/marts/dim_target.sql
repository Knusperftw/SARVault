-- Target dimension: one row per target (human, in scope).
-- payload_class labels each target with its ADC-payload mechanism class,
-- sourced from config/target_set.yml via the target_payload_class seed.
with targets as (
    select * from {{ ref('stg_targets') }}
),

payload_class as (
    select target_chembl_id, payload_class from {{ ref('target_payload_class') }}
)

select
    row_number() over (order by t.target_chembl_id) as target_key,
    t.target_chembl_id,
    t.pref_name,
    t.target_type,
    t.organism,
    pc.payload_class
from targets t
left join payload_class pc on t.target_chembl_id = pc.target_chembl_id
