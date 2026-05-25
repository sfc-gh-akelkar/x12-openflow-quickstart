------------------------------------------------------------------------
-- X12 EDI Pipeline: Prerequisites
-- Run BEFORE setting up Openflow or creating pipeline tables.
------------------------------------------------------------------------

USE ROLE ACCOUNTADMIN;

-- 1. Warehouse (for Dynamic Table refresh)
CREATE WAREHOUSE IF NOT EXISTS APP_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

-- 2. Database and Schemas
CREATE DATABASE IF NOT EXISTS X12_EDI_AI;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.CLAIMS;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.ENROLLMENTS;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.REMITTANCES;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.GOLD;

-- 3. Key Pair Authentication for Openflow PutSnowpipeStreaming
--    Generate locally:
--      openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
--      openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
--    Set on your user:
--      ALTER USER <your_user> SET RSA_PUBLIC_KEY='<paste key without header/footer>';
--    Verify:
--      DESCRIBE USER <your_user>;  -- check RSA_PUBLIC_KEY_FP

-- 4. Network Policy — add your Openflow runtime SPCS IPs
--    Check LOGIN_HISTORY for INCOMING_REQUEST_BLOCKED to find the blocked IPs.
--    ALTER NETWORK POLICY <your_policy> SET ALLOWED_IP_LIST = (..., '153.45.59.0/24');

-- 5. Verify Cortex AI access
SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-sonnet-4-6', 'Say hello') AS test;
