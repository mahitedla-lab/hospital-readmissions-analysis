-- ============================================================================
-- 02  Clean CMS Hospital General Information (one row per hospital).
--     Adds ownership_group, a 4-level grouping of the 10+ CMS ownership labels
--     that is large enough per group for hypothesis testing.
-- ============================================================================
create or replace table staging.hospital_info_clean as
select
    lpad(trim(facility_id), 6, '0')  as facility_id,
    trim(facility_name)              as facility_name,
    upper(trim(state))               as state,
    trim(hospital_type)              as hospital_type,
    trim(hospital_ownership)         as hospital_ownership,
    case
        when hospital_ownership ilike 'Government%'            then 'Government'
        when hospital_ownership ilike 'Voluntary non-profit%'  then 'Non-profit'
        when hospital_ownership ilike 'Proprietary%'           then 'For-profit'
        when hospital_ownership is null or trim(hospital_ownership) = '' then 'Unknown'
        else 'Other'                                           -- Physician, Tribal, etc.
    end as ownership_group
from raw.hospital_info
qualify row_number() over (partition by lpad(trim(facility_id), 6, '0') order by facility_id) = 1;
