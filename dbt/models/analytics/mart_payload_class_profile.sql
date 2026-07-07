-- Payload-class profile (grain: payload_class). Rolls per-compound SAR potency
-- up to each ADC-payload mechanism class so the tubulin and topoisomerase classes
-- compare directly. Backbone of the Payload Classes comparison view (F3.4).
with sar as (
    select
        s.compound_key,
        t.payload_class,
        s.median_pchembl,
        s.max_pchembl,
        s.n_measurements
    from {{ ref('mart_target_sar') }} s
    join {{ ref('dim_target') }} t on s.target_key = t.target_key
    where t.payload_class is not null
)

select
    payload_class,
    count(distinct compound_key)                                    as n_compounds,
    sum(n_measurements)                                             as n_measurements,
    round(median(median_pchembl), 3)                               as median_pchembl,
    round(max(max_pchembl), 3)                                     as max_pchembl,
    round(quantile_cont(median_pchembl, 0.25), 3)                 as p25_pchembl,
    round(quantile_cont(median_pchembl, 0.75), 3)                 as p75_pchembl,
    count(distinct case when max_pchembl >= 9 then compound_key end) as n_sub_nanomolar
from sar
group by payload_class
