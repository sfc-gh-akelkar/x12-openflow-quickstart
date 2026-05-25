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

-- 2. Database
CREATE DATABASE IF NOT EXISTS X12_EDI_AI;

-- 3. Key Pair (generate locally, set public key on user)
--    openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
--    openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
--    ALTER USER <your_user> SET RSA_PUBLIC_KEY='<paste key without header/footer>';

-- 4. Network Policy — add SPCS container CIDR
--    ALTER NETWORK POLICY <your_policy> SET ALLOWED_IP_LIST = ('153.45.59.0/24');

-- 5. Verify Cortex AI access
SELECT AI_COMPLETE('claude-sonnet-4-6', 'Say hello') AS test;
