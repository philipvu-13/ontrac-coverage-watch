USE ROLE ACCOUNTADMIN;
USE WAREHOUSE ontrac_wh;
USE DATABASE ontrac;


-- Q1. Can OnTrac reach 89101, and how fast from each of their facilities?
SELECT origin_sort_center, transit_days, confidence
FROM ontrac.marts.fct_zip_coverage
WHERE zip5 = '89101'
  AND origin_sort_center IS NOT NULL
ORDER BY transit_days;


-- Q2. If I am shipping to 02891, which facility should I inject at?
SELECT zip5, origin_sort_center, transit_days
FROM ontrac.marts.fct_zip_coverage
WHERE zip5 = '02891'
  AND transit_days IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY zip5 ORDER BY transit_days) = 1;


-- Q3. Here are some ZIPs. Which carry a delivery surcharge, and which band?
WITH asked AS (
    SELECT column1 AS zip5 FROM VALUES ('89101'), ('02891'), ('50201'), ('99553'), ('10001')
),
surcharge AS (
    SELECT zip5, surcharge_tier
    FROM ontrac.marts.fct_zip_coverage
    WHERE provenance = 'area_surcharge_pdf'
)
SELECT
    asked.zip5,
    ref.place,
    ref.state,
    COALESCE(surcharge.surcharge_tier, 'no surcharge listed') AS surcharge
FROM asked
LEFT JOIN ontrac.staging.stg_zip_reference ref ON ref.zip5 = asked.zip5
LEFT JOIN surcharge ON surcharge.zip5 = asked.zip5
ORDER BY asked.zip5;


-- Q4. What has changed since the previous capture?
SELECT captured_on, compared_to, source, added, removed, changed, summary
FROM ontrac.marts.alert_change_summary
ORDER BY captured_on DESC;


-- Q5. Where did those changes land geographically?
SELECT ref.state, changes.change_type, COUNT(*) AS zips
FROM ontrac.marts.fct_zip_surcharge_changes changes
JOIN ontrac.staging.stg_zip_reference ref ON ref.zip5 = changes.zip5
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 20;


-- Q6. Where do OnTrac's own two sources disagree?
WITH map_states AS (
    SELECT DISTINCT state
    FROM ontrac.staging.stg_map_coverage
    WHERE outcome NOT IN ('unserved', 'no_data')
      AND captured_on = (SELECT MAX(captured_on) FROM ontrac.staging.stg_map_coverage)
),
surcharge_states AS (
    SELECT ref.state, COUNT(*) AS zips
    FROM ontrac.staging.stg_zip_surcharge surcharge
    JOIN ontrac.staging.stg_zip_reference ref ON ref.zip5 = surcharge.zip5
    WHERE surcharge.captured_on = (SELECT MAX(captured_on) FROM ontrac.staging.stg_zip_surcharge)
    GROUP BY 1
)
SELECT surcharge_states.state, surcharge_states.zips AS surcharged_zips
FROM surcharge_states
LEFT JOIN map_states ON map_states.state = surcharge_states.state
WHERE map_states.state IS NULL
ORDER BY 2 DESC;


-- Q7. Any live disruptions, and do they hit areas OnTrac says it serves?
SELECT
    alerts.posted_date,
    alerts.event_type,
    alerts.cause,
    alerts.state,
    alerts.cities,
    alerts.summary,
    CASE WHEN served.state IS NULL THEN 'not on the coverage map' ELSE 'served' END AS coverage_status
FROM ontrac.marts.fct_service_alert_states alerts
LEFT JOIN (
    SELECT DISTINCT state
    FROM ontrac.staging.stg_map_coverage
    WHERE outcome NOT IN ('unserved', 'no_data')
      AND captured_on = (SELECT MAX(captured_on) FROM ontrac.staging.stg_map_coverage)
) served ON served.state = alerts.state
ORDER BY alerts.posted_date DESC;