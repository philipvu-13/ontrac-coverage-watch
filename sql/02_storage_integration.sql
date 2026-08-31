USE ROLE ACCOUNTADMIN;

CREATE STORAGE INTEGRATION IF NOT EXISTS ontrac_s3_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::751479507701:role/snowflake-ontrac-s3-access'
  STORAGE_ALLOWED_LOCATIONS = ('s3://unclephil-ontrac-coverage-raw/structured/');

DESC INTEGRATION ontrac_s3_integration;