------------------------------------------------------------------------
-- X12 EDI Pipeline: Gold Layer (AI Enrichment)
-- Data arrives already structured from ParseX12ToJSON.
-- Gold layer adds: type casting, AI diagnosis enrichment, analytics views.
------------------------------------------------------------------------

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE APP_WH;

CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.GOLD;

------------------------------------------------------------------------
-- GOLD: Claims with AI-enriched diagnosis
-- Adds human-readable diagnosis descriptions via Claude Sonnet 4-6
------------------------------------------------------------------------
CREATE OR REPLACE DYNAMIC TABLE X12_EDI_AI.GOLD.GOLD_CLAIMS
    TARGET_LAG = '10 minutes'
    WAREHOUSE = APP_WH
AS
WITH base AS (
    SELECT
        claim_id,
        TRY_TO_DECIMAL(claim_amount, 12, 2) AS claim_amount,
        place_of_service_code,
        subscriber_last_name,
        subscriber_first_name,
        subscriber_id,
        TRY_TO_DATE(patient_dob, 'YYYYMMDD') AS patient_dob,
        patient_gender,
        billing_provider_last_name,
        billing_provider_npi,
        rendering_provider_last_name,
        rendering_provider_npi,
        SPLIT_PART(diagnosis_code_1, ':', 2) AS primary_diagnosis_code,
        SPLIT_PART(procedure_code, ':', 2) AS primary_procedure_code,
        TRY_TO_DECIMAL(service_charge_amount, 12, 2) AS service_charge_amount,
        TRY_TO_DATE(service_date, 'YYYYMMDD') AS service_date,
        payer_responsibility_sequence,
        subscriber_group_name,
        interchange_sender_id,
        interchange_receiver_id
    FROM X12_EDI_AI.CLAIMS.LANDING_837_CLAIMS
    WHERE claim_id IS NOT NULL
)
SELECT
    b.*,
    TRY_PARSE_JSON(
        AI_COMPLETE('claude-sonnet-4-6',
            'You are a medical coding expert. Given this ICD-10 code, return a JSON object with keys: '
            || '"description" (human-readable diagnosis name), '
            || '"category" (Respiratory, Cardiovascular, Musculoskeletal, Endocrine, Gastrointestinal, Infectious, Neoplasm, Injury, Mental Health, Other), '
            || '"chronic" (true/false). Return ONLY valid JSON. ICD-10 code: '
            || COALESCE(b.primary_diagnosis_code, 'Z00.00')
        )
    ):description::VARCHAR AS diagnosis_description,
    TRY_PARSE_JSON(
        AI_COMPLETE('claude-sonnet-4-6',
            'You are a medical coding expert. Given this ICD-10 code, return a JSON object with keys: '
            || '"description" (human-readable diagnosis name), '
            || '"category" (Respiratory, Cardiovascular, Musculoskeletal, Endocrine, Gastrointestinal, Infectious, Neoplasm, Injury, Mental Health, Other), '
            || '"chronic" (true/false). Return ONLY valid JSON. ICD-10 code: '
            || COALESCE(b.primary_diagnosis_code, 'Z00.00')
        )
    ):category::VARCHAR AS diagnosis_category,
    TRY_PARSE_JSON(
        AI_COMPLETE('claude-sonnet-4-6',
            'You are a medical coding expert. Given this ICD-10 code, return a JSON object with keys: '
            || '"description" (human-readable diagnosis name), '
            || '"category" (Respiratory, Cardiovascular, Musculoskeletal, Endocrine, Gastrointestinal, Infectious, Neoplasm, Injury, Mental Health, Other), '
            || '"chronic" (true/false). Return ONLY valid JSON. ICD-10 code: '
            || COALESCE(b.primary_diagnosis_code, 'Z00.00')
        )
    ):chronic::BOOLEAN AS is_chronic_condition
FROM base b;

------------------------------------------------------------------------
-- GOLD: Enrollments (typed, no AI needed)
------------------------------------------------------------------------
CREATE OR REPLACE DYNAMIC TABLE X12_EDI_AI.GOLD.GOLD_ENROLLMENTS
    TARGET_LAG = '10 minutes'
    WAREHOUSE = APP_WH
AS
SELECT
    member_id,
    member_last_name,
    member_first_name,
    member_middle_name,
    TRY_TO_DATE(member_dob, 'YYYYMMDD') AS member_dob,
    member_gender,
    member_marital_status,
    member_address_line_1,
    member_city,
    member_state,
    member_zip,
    benefit_status,
    maintenance_type_code,
    maintenance_reason_code,
    employment_status_code,
    insurance_line_code,
    plan_coverage_description,
    coverage_level_code,
    TRY_TO_DATE(coverage_start_date, 'YYYYMMDD') AS coverage_start_date,
    TRY_TO_DATE(coverage_end_date, 'YYYYMMDD') AS coverage_end_date,
    TRY_TO_DATE(maintenance_effective_date, 'YYYYMMDD') AS maintenance_effective_date,
    interchange_sender_id,
    interchange_receiver_id
FROM X12_EDI_AI.ENROLLMENTS.LANDING_834_ENROLLMENTS
WHERE member_id IS NOT NULL;

------------------------------------------------------------------------
-- GOLD: Remittances (typed + payment analytics)
------------------------------------------------------------------------
CREATE OR REPLACE DYNAMIC TABLE X12_EDI_AI.GOLD.GOLD_REMITTANCES
    TARGET_LAG = '10 minutes'
    WAREHOUSE = APP_WH
AS
SELECT
    claim_id,
    claim_status_code,
    TRY_TO_DECIMAL(claim_charge_amount, 12, 2) AS claim_charge_amount,
    TRY_TO_DECIMAL(claim_payment_amount, 12, 2) AS claim_payment_amount,
    TRY_TO_DECIMAL(patient_responsibility_amount, 12, 2) AS patient_responsibility_amount,
    TRY_TO_DECIMAL(claim_charge_amount, 12, 2) - TRY_TO_DECIMAL(claim_payment_amount, 12, 2) AS adjustment_total,
    payer_claim_control_number,
    patient_last_name,
    patient_first_name,
    patient_id,
    rendering_provider_last_name,
    rendering_provider_npi,
    SPLIT_PART(procedure_code, ':', 2) AS procedure_code,
    TRY_TO_DECIMAL(service_charge_amount, 12, 2) AS service_charge_amount,
    TRY_TO_DECIMAL(service_payment_amount, 12, 2) AS service_payment_amount,
    TRY_TO_DECIMAL(allowed_amount, 12, 2) AS allowed_amount,
    adjustment_group_code,
    adjustment_reason_code_1,
    TRY_TO_DECIMAL(adjustment_amount_1, 12, 2) AS adjustment_amount_1,
    TRY_TO_DATE(service_date, 'YYYYMMDD') AS service_date,
    interchange_sender_id,
    interchange_receiver_id
FROM X12_EDI_AI.REMITTANCES.LANDING_835_REMITTANCES
WHERE claim_id IS NOT NULL;

------------------------------------------------------------------------
-- SAMPLE ANALYTICS QUERIES
------------------------------------------------------------------------

-- Claims by diagnosis category
-- SELECT diagnosis_category, COUNT(*) AS claims, AVG(claim_amount) AS avg_billed
-- FROM X12_EDI_AI.GOLD.GOLD_CLAIMS
-- GROUP BY 1 ORDER BY 2 DESC;

-- Payment variance analysis
-- SELECT claim_id, claim_charge_amount, claim_payment_amount, adjustment_total,
--        adjustment_group_code, adjustment_reason_code_1
-- FROM X12_EDI_AI.GOLD.GOLD_REMITTANCES
-- WHERE adjustment_total > 100
-- ORDER BY adjustment_total DESC LIMIT 20;

-- Enrollment activity
-- SELECT maintenance_type_code, plan_coverage_description, COUNT(*) AS member_actions
-- FROM X12_EDI_AI.GOLD.GOLD_ENROLLMENTS
-- GROUP BY 1, 2 ORDER BY 3 DESC;
