USE ROLE ACCOUNTADMIN;
USE WAREHOUSE ontrac_wh;
USE DATABASE ontrac;
USE SCHEMA raw;

CREATE TABLE IF NOT EXISTS ontrac.raw.service_alerts (
  captured_on DATE,
  characters INTEGER,
  provenance STRING,
  confidence STRING,
  source_key STRING,
  alert_text STRING,
  dt DATE,
  source_file STRING
);

COPY INTO ontrac.raw.zip_surcharge
FROM (
  SELECT
    $1::STRING, $2::STRING, $3::DATE, $4::INTEGER, $5::STRING, $6::STRING,
    REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9]{4}-[0-9]{2}-[0-9]{2})', 1, 1, 'e', 1)::DATE,
    METADATA$FILENAME
  FROM @ontrac_structured
)
PATTERN = '.*source=zip-surcharge/.*rows[.]csv'
ON_ERROR = ABORT_STATEMENT;

COPY INTO ontrac.raw.map_coverage
FROM (
  SELECT
    $1::STRING, $2::STRING, $3::INTEGER, $4::STRING, $5::STRING,
    $6::INTEGER, $7::INTEGER, $8::STRING, $9::STRING, $10::STRING,
    $11::DATE, $12::STRING,
    METADATA$FILENAME
  FROM @ontrac_structured
)
PATTERN = '.*source=coverage-maps/.*rows[.]csv'
ON_ERROR = ABORT_STATEMENT;

COPY INTO ontrac.raw.service_alerts
FROM (
  SELECT
    $1::DATE, $2::INTEGER, $3::STRING, $4::STRING, $5::STRING, $6::STRING,
    REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9]{4}-[0-9]{2}-[0-9]{2})', 1, 1, 'e', 1)::DATE,
    METADATA$FILENAME
  FROM @ontrac_structured
)
PATTERN = '.*source=service-alerts/.*rows[.]csv'
ON_ERROR = ABORT_STATEMENT;

SELECT 'zip_surcharge' AS table_name, dt, COUNT(*) AS row_count FROM ontrac.raw.zip_surcharge GROUP BY 1, 2
UNION ALL
SELECT 'map_coverage', dt, COUNT(*) FROM ontrac.raw.map_coverage GROUP BY 1, 2
UNION ALL
SELECT 'service_alerts', dt, COUNT(*) FROM ontrac.raw.service_alerts GROUP BY 1, 2
ORDER BY 1, 2;