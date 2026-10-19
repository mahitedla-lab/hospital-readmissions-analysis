-- ============================================================================
-- 04  One row per hospital: overall performance, penalty exposure and size tier.
--
--   total_discharges     sum of HRRP-measured discharges across the hospital's conditions.
--                        CMS General Information has no bed count, so this is the size proxy.
--   size_tier            terciles of total_discharges: Small / Medium / Large
--   has_penalty_exposure 1 if ERR > 1 on at least one condition
--   weighted_err         ERR averaged across conditions, weighted by discharges
-- ============================================================================
create or replace table analysis.hospital_summary as
with agg as (
    select
        facility_id,
        any_value(facility_name)       as facility_name,
        any_value(state)               as state,
        any_value(hospital_type)       as hospital_type,
        any_value(hospital_ownership)  as hospital_ownership,
        any_value(ownership_group)     as ownership_group,
        count(*)                       as n_conditions,
        avg(excess_readmission_ratio)  as mean_err,
        max(excess_readmission_ratio)  as max_err,
        sum(err_above_1)               as n_conditions_above_1,
        sum(number_of_discharges)      as total_discharges,
        sum(excess_readmission_ratio * number_of_discharges)
            / nullif(sum(case when excess_readmission_ratio is not null then number_of_discharges end), 0) as weighted_err
    from analysis.hospital_condition
    group by facility_id
),
cuts as (
    select
        quantile_cont(total_discharges, 1.0 / 3) as q_small,
        quantile_cont(total_discharges, 2.0 / 3) as q_medium
    from agg
    where total_discharges is not null
)
select
    agg.*,
    case
        when agg.total_discharges is null           then 'Unknown'
        when agg.total_discharges <= cuts.q_small   then 'Small'
        when agg.total_discharges <= cuts.q_medium  then 'Medium'
        else 'Large'
    end as size_tier,
    case when agg.n_conditions_above_1 > 0 then 1 else 0 end as has_penalty_exposure
from agg
cross join cuts;
