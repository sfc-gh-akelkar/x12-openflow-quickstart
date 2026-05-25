------------------------------------------------------------------------
-- X12 EDI Pipeline: Prerequisites
-- Run this BEFORE setting up Openflow or creating the pipeline tables.
-- Requires: ACCOUNTADMIN role
------------------------------------------------------------------------

USE ROLE ACCOUNTADMIN;

------------------------------------------------------------------------
-- 1. WAREHOUSE (used by Dynamic Tables for refresh)
------------------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS APP_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

------------------------------------------------------------------------
-- 2. DATABASE & SCHEMAS
------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS X12_EDI_AI;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.STAGING;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.SILVER;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.GOLD;

------------------------------------------------------------------------
-- 3. KEY PAIR AUTHENTICATION (required for Snowpipe Streaming)
--    Generate a key pair locally:
--      openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
--      openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
--    Then set the public key on your user:
------------------------------------------------------------------------
-- ALTER USER <your_user> SET RSA_PUBLIC_KEY='<paste public key without header/footer>';

------------------------------------------------------------------------
-- 4. NETWORK POLICY
--    SPCS containers use rotating IPs. Add a /24 CIDR block.
--    First, start your Openflow runtime and check the error log for the
--    blocked IP, then add that IP's /24 range here.
------------------------------------------------------------------------
-- Example: If blocked IP is 153.45.59.132, add the /24:
--
-- CREATE NETWORK RULE IF NOT EXISTS X12_EDI_AI.STAGING.SPCS_EGRESS_RULE
--     TYPE = IPV4
--     VALUE_LIST = ('153.45.59.0/24')
--     MODE = EGRESS;
--
-- Or add to an existing network policy:
-- ALTER NETWORK POLICY <your_policy> SET ALLOWED_IP_LIST = (
--     '0.0.0.0/0'  -- or your existing allowed IPs
--     ,'153.45.59.0/24'  -- SPCS container range
-- );

------------------------------------------------------------------------
-- 5. EXTERNAL ACCESS INTEGRATION (for Openflow to reach S3)
--    Your Openflow deployment likely already has this. If not:
------------------------------------------------------------------------
-- CREATE OR REPLACE NETWORK RULE ALLOW_ALL_RULE
--     TYPE = HOST_PORT
--     VALUE_LIST = ('0.0.0.0:443', '0.0.0.0:80')
--     MODE = EGRESS;
--
-- CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION ALLOW_ALL_EAI
--     ALLOWED_NETWORK_RULES = (ALLOW_ALL_RULE)
--     ENABLED = TRUE;

------------------------------------------------------------------------
-- 6. S3 STORAGE INTEGRATION (optional - for Snowpipe auto-ingest later)
------------------------------------------------------------------------
-- CREATE OR REPLACE STORAGE INTEGRATION S3_X12_INTEGRATION
--     TYPE = EXTERNAL_STAGE
--     STORAGE_PROVIDER = 'S3'
--     ENABLED = TRUE
--     STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<account>:role/<role>'
--     STORAGE_ALLOWED_LOCATIONS = ('s3://<your-bucket>/x12/');

------------------------------------------------------------------------
-- 7. VERIFY CORTEX AI ACCESS
------------------------------------------------------------------------
SELECT AI_COMPLETE('claude-sonnet-4-6', 'Say hello') AS test;
-- If this fails, your account/region may not have Claude Sonnet 4-6.
-- Fallback options: 'llama3.3-70b' or 'mistral-large2'

------------------------------------------------------------------------
-- DONE. Next steps:
-- 1. Upload sample_837p_20_claims.edi to your S3 bucket under x12/ prefix
-- 2. Set up Openflow (see README.md for processor-by-processor walkthrough)
-- 3. Run 01_x12_pipeline.sql to create the landing table + Dynamic Tables
------------------------------------------------------------------------
