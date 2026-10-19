-- ============================================================================
-- 99  Data-quality and reconciliation checks, kept as a table so each run is auditable.
--     Print with:  select * from analysis.data_checks;
-- ============================================================================
create or replace table analysis.data_checks as
select 'hrrp_raw_rows' as check_name, count(*)::bigint as value, 'rows loaded from the HRRP CSV' as note
from raw.hrrp
union all
select 'hrrp_rows_after_cleaning', count(*), 'six HRRP measures, one row per hospital x measure'
from staging.hrrp_clean
union all
select 'hrrp_rows_without_ratio', count(*), 'suppressed by CMS (too few cases / not available); excluded from analysis'
from staging.hrrp_clean where excess_readmission_ratio is null
union all
select 'hospital_condition_rows', count(*), 'hospital x condition results used in the analysis'
from analysis.hospital_condition
union all
select 'hospitals_in_hrrp', count(distinct facility_id), 'distinct hospitals in the cleaned HRRP data'
from staging.hrrp_clean
union all
select 'hospitals_analysed', count(*), 'hospitals with at least one published ERR'
from analysis.hospital_summary
union all
select 'hospitals_not_in_general_info', count(distinct facility_id), 'HRRP hospitals with no Hospital General Information match (ownership = Unknown)'
from analysis.hospital_condition where not matched_hospital_info
union all
select 'state_mismatches', count(*), 'HRRP state differs from General Information state'
from staging.hrrp_clean as h
inner join staging.hospital_info_clean as i on h.facility_id = i.facility_id
where h.state <> i.state
union all
select 'states_covered', count(distinct state), 'states / territories present'
from analysis.hospital_condition
union all
select 'conditions_covered', count(distinct condition), 'expected: 6'
from analysis.hospital_condition
union all
select 'err_out_of_range', count(*), 'ERR below 0 or above 3 (implausible)'
from analysis.hospital_condition
where excess_readmission_ratio < 0 or excess_readmission_ratio > 3
union all
select 'hospitals_unknown_size', count(*), 'no discharge counts, so no size tier'
from analysis.hospital_summary where size_tier = 'Unknown';
