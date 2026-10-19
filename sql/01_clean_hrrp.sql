-- ============================================================================
-- 01  Clean the CMS Hospital Readmissions Reduction Program (HRRP) data.
--     One row per hospital x condition. Source: raw.hrrp (all text).
--
--     * IDs are zero-padded to 6 characters so they join to Hospital General Information.
--     * CMS writes "N/A" / "Too Few to Report" for suppressed values -> NULL via try_cast.
--     * The six HRRP measures are given readable condition names.
--     * If a hospital/measure appears more than once, the latest reporting period wins.
-- ============================================================================
create schema if not exists staging;

create or replace table staging.hrrp_clean as
with typed as (
    select
        lpad(trim(facility_id), 6, '0')                                           as facility_id,
        trim(facility_name)                                                       as facility_name,
        upper(trim(state))                                                        as state,
        trim(measure_name)                                                        as measure_code,
        try_cast(replace(trim(number_of_discharges), ',', '') as integer)         as number_of_discharges,
        try_cast(trim(excess_readmission_ratio) as double)                        as excess_readmission_ratio,
        try_cast(trim(predicted_readmission_rate) as double)                      as predicted_readmission_rate,
        try_cast(trim(expected_readmission_rate) as double)                       as expected_readmission_rate,
        try_cast(replace(trim(number_of_readmissions), ',', '') as integer)       as number_of_readmissions,
        trim(footnote)                                                            as footnote,
        cast(coalesce(try_strptime(trim(start_date), '%m/%d/%Y'),
                      try_strptime(trim(start_date), '%Y-%m-%d')) as date)        as period_start,
        cast(coalesce(try_strptime(trim(end_date), '%m/%d/%Y'),
                      try_strptime(trim(end_date), '%Y-%m-%d')) as date)          as period_end
    from raw.hrrp
)
select
    typed.*,
    case measure_code
        when 'READM-30-AMI-HRRP'      then 'Acute Myocardial Infarction (AMI)'
        when 'READM-30-CABG-HRRP'     then 'Coronary Artery Bypass Graft (CABG)'
        when 'READM-30-COPD-HRRP'     then 'Chronic Obstructive Pulmonary Disease (COPD)'
        when 'READM-30-HF-HRRP'       then 'Heart Failure (HF)'
        when 'READM-30-HIP-KNEE-HRRP' then 'Hip/Knee Arthroplasty'
        when 'READM-30-PN-HRRP'       then 'Pneumonia (PN)'
    end as condition
from typed
where measure_code in (
    'READM-30-AMI-HRRP', 'READM-30-CABG-HRRP', 'READM-30-COPD-HRRP',
    'READM-30-HF-HRRP', 'READM-30-HIP-KNEE-HRRP', 'READM-30-PN-HRRP'
)
qualify row_number() over (
    partition by facility_id, measure_code
    order by period_end desc nulls last
) = 1;
