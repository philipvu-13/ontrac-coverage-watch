-- Evidence for the Cortex claim in the README.
-- Run against a Snowflake trial account this returns
--   "AI function COMPLETE is not available for trial accounts"
-- rather than a result. Verified 2026-08-30.
-- This is why the LLM step runs against the Anthropic API instead,
-- and why fct_service_alerts_cortex.sql is committed as .disabled.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE ontrac_wh;

SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', 'Reply with the single word ok.') AS probe;