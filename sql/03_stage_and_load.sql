-- SETUP ONLY, RUN ONCE.
-- The CREATE OR REPLACE statements below will drop and recreate the raw
-- tables, discarding every capture already loaded. For loading new captures
-- into existing tables, use 10_load_new_captures.sql, or just run dbt build,
-- which does the same loads as on-run-start hooks.

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE ontrac_wh;
USE DATABASE ontrac;
USE SCHEMA raw;

CREATE OR REPLACE FILE FORMAT ontrac_csv
  TYPE = CSV
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('')
  EMPTY_FIELD_AS_NULL = TRUE;

CREATE OR REPLACE STAGE ontrac_structured
  STORAGE_INTEGRATION = ontrac_s3_integration
  URL = 's3://unclephil-ontrac-coverage-raw/structured/'
  FILE_FORMAT = ontrac_csv;

LIST @ontrac_structured;

CREATE OR REPLACE TABLE ontrac.raw.zip_surcharge (
  zip5 STRING,
  tier STRING,
  effective_date DATE,
  page INTEGER,
  provenance STRING,
  confidence STRING,
  dt DATE,
  source_file STRING
);

CREATE OR REPLACE TABLE ontrac.raw.map_coverage (
  sort_center STRING,
  sort_center_state STRING,
  map_index INTEGER,
  state STRING,
  outcome STRING,
  points_total INTEGER,
  points_agreeing INTEGER,
  split STRING,
  provenance STRING,
  confidence STRING,
  dt DATE,
  source_key STRING,
  source_file STRING
);

CREATE OR REPLACE TABLE ontrac.raw.zip_reference (
  zip5 STRING,
  state STRING,
  state_name STRING,
  place STRING,
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

COPY INTO ontrac.raw.zip_reference
FROM (
  SELECT
    $1::STRING, $2::STRING, $3::STRING, $4::STRING,
    REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9]{4}-[0-9]{2}-[0-9]{2})', 1, 1, 'e', 1)::DATE,
    METADATA$FILENAME
  FROM @ontrac_structured
)
PATTERN = '.*source=zip-reference/.*rows[.]csv'
ON_ERROR = ABORT_STATEMENT;

SELECT 'zip_surcharge' AS table_name, dt, COUNT(*) AS row_count FROM ontrac.raw.zip_surcharge GROUP BY 1, 2
UNION ALL
SELECT 'map_coverage', dt, COUNT(*) FROM ontrac.raw.map_coverage GROUP BY 1, 2
UNION ALL
SELECT 'zip_reference', dt, COUNT(*) FROM ontrac.raw.zip_reference GROUP BY 1, 2
ORDER BY 1, 2;