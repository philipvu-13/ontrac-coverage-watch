USE ROLE ACCOUNTADMIN;
USE WAREHOUSE ontrac_wh;
USE DATABASE ontrac;
USE SCHEMA raw;

CREATE TABLE IF NOT EXISTS ontrac.raw.service_alerts_parsed (
  captured_on DATE,
  event_type STRING,
  cause STRING,
  posted_date DATE,
  states STRING,
  cities STRING,
  summary STRING,
  provenance STRING,
  confidence STRING,
  model STRING,
  source_key STRING,
  dt DATE,
  source_file STRING
);

COPY INTO ontrac.raw.service_alerts_parsed
FROM (
  SELECT
    $1::DATE, $2::STRING, $3::STRING, $4::DATE, $5::STRING, $6::STRING, $7::STRING,
    $8::STRING, $9::STRING, $10::STRING, $11::STRING,
    REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9]{4}-[0-9]{2}-[0-9]{2})', 1, 1, 'e', 1)::DATE,
    METADATA$FILENAME
  FROM @ontrac_structured
)
PATTERN = '.*source=service-alerts-parsed/.*rows[.]csv'
ON_ERROR = ABORT_STATEMENT;

SELECT * FROM ontrac.raw.service_alerts_parsed;