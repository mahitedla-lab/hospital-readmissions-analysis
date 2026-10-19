-- ============================================================================
-- 03  Merge HRRP results with Hospital General Information.
--     Grain: one row per hospital x condition that has a published excess
--     readmission ratio (ERR). ERR > 1 means more readmissions than expected for
--     that hospital's case mix, which is what exposes it to an HRRP payment penalty.
--     HRRP is the left side: hospitals with no HGI match are kept and labelled 'Unknown'.
-- ============================================================================
create schema if not exists analysis;

create or replace table analysis.hospital_condition as
select
    h.facility_id,
    coalesce(i.facility_name, h.facility_name)       as facility_name,
    h.state,
    i.hospital_type,
    i.hospital_ownership,
    coalesce(i.ownership_group, 'Unknown')           as ownership_group,
    h.measure_code,
    h.condition,
    h.number_of_discharges,
    h.number_of_readmissions,
    h.predicted_readmission_rate,
    h.expected_readmission_rate,
    h.excess_readmission_ratio,
    case when h.excess_readmission_ratio > 1 then 1 else 0 end as err_above_1,
    h.footnote,
    h.period_start,
    h.period_end,
    i.facility_id is not null                        as matched_hospital_info
from staging.hrrp_clean as h
left join staging.hospital_info_clean as i
    on h.facility_id = i.facility_id
where h.excess_readmission_ratio is not null;
