-- ============================================================================
-- 05  Summary tables for the dashboard and the write-up.
--     pct_* columns are fractions (0-1); format as percentages in Tableau.
-- ============================================================================

-- Nationwide, by condition ----------------------------------------------------
create or replace table analysis.condition_summary as
select
    condition,
    count(*)                              as hospitals,
    avg(excess_readmission_ratio)         as mean_err,
    median(excess_readmission_ratio)      as median_err,
    avg(err_above_1)                      as pct_above_1,
    sum(number_of_discharges)             as discharges
from analysis.hospital_condition
group by condition;

-- By state x condition (the map / heatmap in the dashboard) -------------------------
create or replace table analysis.state_condition_summary as
select
    state,
    condition,
    count(*)                              as hospitals,
    avg(excess_readmission_ratio)         as mean_err,
    median(excess_readmission_ratio)      as median_err,
    avg(err_above_1)                      as pct_above_1,
    sum(number_of_discharges)             as discharges
from analysis.hospital_condition
group by state, condition;

-- By state, all conditions together -------------------------------------------------
create or replace table analysis.state_summary as
select
    state,
    count(*)                              as hospitals,
    avg(mean_err)                         as mean_hospital_err,
    median(mean_err)                      as median_hospital_err,
    avg(has_penalty_exposure)             as pct_hospitals_exposed,
    avg(n_conditions_above_1)             as avg_conditions_above_1
from analysis.hospital_summary
group by state;

-- Condition x ownership -------------------------------------------------------------
create or replace table analysis.condition_ownership_summary as
select
    condition,
    ownership_group,
    count(*)                              as hospitals,
    avg(excess_readmission_ratio)         as mean_err,
    median(excess_readmission_ratio)      as median_err,
    avg(err_above_1)                      as pct_above_1
from analysis.hospital_condition
group by condition, ownership_group;

-- Segment penalty risk: which kinds of hospitals carry the most exposure ------------------
--   pct_hospitals_exposed        share of hospitals with ERR > 1 on at least one condition
--   pct_condition_pairs_above_1  share of hospital-condition results with ERR > 1
create or replace table analysis.segment_risk as
with segments as (
    select 'Ownership' as segment_type, ownership_group as segment, h.*
    from analysis.hospital_summary as h
    union all
    select 'Size', size_tier, h.*
    from analysis.hospital_summary as h
    where size_tier <> 'Unknown'
    union all
    select 'Ownership x Size', ownership_group || ' / ' || size_tier, h.*
    from analysis.hospital_summary as h
    where size_tier <> 'Unknown'
)
select
    segment_type,
    segment,
    count(*)                                              as hospitals,
    avg(has_penalty_exposure)                             as pct_hospitals_exposed,
    avg(mean_err)                                         as mean_hospital_err,
    median(mean_err)                                      as median_hospital_err,
    sum(n_conditions_above_1) * 1.0 / sum(n_conditions)   as pct_condition_pairs_above_1,
    avg(n_conditions_above_1)                             as avg_conditions_above_1,
    rank() over (
        partition by segment_type
        order by avg(has_penalty_exposure) desc, avg(mean_err) desc
    )                                                     as risk_rank
from segments
group by segment_type, segment;
