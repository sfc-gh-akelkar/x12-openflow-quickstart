------------------------------------------------------------------------
-- X12 EDI Pipeline: Gold Layer
-- Dynamic Tables with continuous refresh from landing tables.
-- Adds: type casting, claims-remittance join, code lookups, AI enrichment.
------------------------------------------------------------------------

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE APP_WH;

CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.GOLD;

------------------------------------------------------------------------
-- GOLD: Claims joined with Remittances + payment analytics
------------------------------------------------------------------------
CREATE OR REPLACE DYNAMIC TABLE X12_EDI_AI.GOLD.GOLD_CLAIMS
    TARGET_LAG = '1 minute'
    WAREHOUSE = APP_WH
AS
SELECT
    c.claim_id,
    TRY_TO_DOUBLE(c.claim_amount) as claim_amount,
    c.subscriber_last_name,
    c.subscriber_first_name,
    c.subscriber_id,
    c.diagnosis_code_1,
    c.procedure_code,
    SPLIT_PART(c.service_date, ';', 1) as service_date,
    c.billing_provider_last_name,
    c.billing_provider_npi,
    c.payer_responsibility_sequence,
    c.claim_filing_indicator,
    TRY_TO_DOUBLE(r.claim_payment_amount) as payment_amount,
    TRY_TO_DOUBLE(SPLIT_PART(r.patient_responsibility_amount, ';', 1)) as patient_responsibility,
    SPLIT_PART(r.adjustment_group_code, ';', 1) as adjustment_group_code,
    r.adjustment_reason_code_1,
    TRY_TO_DOUBLE(SPLIT_PART(r.adjustment_amount_1, ';', 1)) as adjustment_amount,
    TRY_TO_DOUBLE(SPLIT_PART(r.allowed_amount, ';', 1)) as allowed_amount,
    COALESCE(TRY_TO_DOUBLE(c.claim_amount), 0) - COALESCE(TRY_TO_DOUBLE(r.claim_payment_amount), 0) as underpayment_amount,
    CASE WHEN r.claim_id IS NOT NULL THEN 'PAID' ELSE 'PENDING' END as payment_status,
    c.interchange_date as file_date,
    c.transaction_set_control_number
FROM X12_EDI_AI.CLAIMS.LANDING_837_CLAIMS c
LEFT JOIN X12_EDI_AI.REMITTANCES.LANDING_835_REMITTANCES r
    ON c.claim_id = r.claim_id;

------------------------------------------------------------------------
-- GOLD: Enrollments (typed + code descriptions)
------------------------------------------------------------------------
CREATE OR REPLACE DYNAMIC TABLE X12_EDI_AI.GOLD.GOLD_ENROLLMENTS
    TARGET_LAG = '1 minute'
    WAREHOUSE = APP_WH
AS
SELECT
    e.member_id,
    e.member_last_name,
    e.member_first_name,
    e.member_city,
    e.member_state,
    e.member_zip,
    e.member_dob,
    e.member_gender,
    e.benefit_status,
    e.individual_relationship_code,
    e.maintenance_type_code,
    e.maintenance_reason_code,
    e.employment_status_code,
    e.coverage_start_date,
    e.coverage_end_date,
    e.insurance_line_code,
    e.plan_coverage_description,
    e.coverage_level_code,
    e.reference_id,
    e.interchange_date as file_date,
    e.transaction_set_control_number,
    CASE
        WHEN e.benefit_status = '024' THEN 'ACTIVE'
        WHEN e.benefit_status = '025' THEN 'COBRA'
        WHEN e.benefit_status = '030' THEN 'TERMINATED'
        ELSE e.benefit_status
    END as enrollment_status_desc,
    CASE
        WHEN e.individual_relationship_code = '18' THEN 'SELF'
        WHEN e.individual_relationship_code = '01' THEN 'SPOUSE'
        WHEN e.individual_relationship_code = '19' THEN 'CHILD'
        ELSE e.individual_relationship_code
    END as relationship_desc
FROM X12_EDI_AI.ENROLLMENTS.LANDING_834_ENROLLMENTS e;

------------------------------------------------------------------------
-- GOLD: Remittances (typed + status descriptions)
------------------------------------------------------------------------
CREATE OR REPLACE DYNAMIC TABLE X12_EDI_AI.GOLD.GOLD_REMITTANCES
    TARGET_LAG = '1 minute'
    WAREHOUSE = APP_WH
AS
SELECT
    r.claim_id,
    TRY_TO_DOUBLE(r.claim_charge_amount) as charge_amount,
    TRY_TO_DOUBLE(r.claim_payment_amount) as payment_amount,
    TRY_TO_DOUBLE(SPLIT_PART(r.patient_responsibility_amount, ';', 1)) as patient_responsibility,
    r.claim_status_code,
    r.patient_last_name,
    r.patient_first_name,
    r.rendering_provider_last_name,
    r.rendering_provider_npi,
    r.procedure_code,
    SPLIT_PART(r.service_date, ';', 1) as service_date,
    SPLIT_PART(r.adjustment_group_code, ';', 1) as primary_adjustment_group,
    r.adjustment_reason_code_1,
    TRY_TO_DOUBLE(SPLIT_PART(r.adjustment_amount_1, ';', 1)) as primary_adjustment_amount,
    TRY_TO_DOUBLE(SPLIT_PART(r.allowed_amount, ';', 1)) as allowed_amount,
    CASE r.claim_status_code
        WHEN '1' THEN 'PROCESSED_PRIMARY'
        WHEN '2' THEN 'PROCESSED_SECONDARY'
        WHEN '3' THEN 'PROCESSED_TERTIARY'
        WHEN '4' THEN 'DENIED'
        WHEN '22' THEN 'REVERSAL'
        ELSE r.claim_status_code
    END as claim_status_desc,
    r.interchange_date as file_date,
    r.transaction_set_control_number
FROM X12_EDI_AI.REMITTANCES.LANDING_835_REMITTANCES r;

------------------------------------------------------------------------
-- GOLD: AI-Enriched Claims View
-- Uses Cortex AI to classify diagnosis codes by clinical specialty
------------------------------------------------------------------------
CREATE OR REPLACE VIEW X12_EDI_AI.GOLD.GOLD_CLAIMS_AI_ENRICHED AS
SELECT
    gc.*,
    SNOWFLAKE.CORTEX.COMPLETE('claude-sonnet-4-6',
        'Given ICD-10 diagnosis code "' || gc.diagnosis_code_1 || '", respond with ONLY the medical specialty name (e.g., Cardiology, Orthopedics, Internal Medicine). One or two words max.'
    ) as clinical_specialty,
    SNOWFLAKE.CORTEX.COMPLETE('claude-sonnet-4-6',
        'Given ICD-10 code "' || gc.diagnosis_code_1 || '", provide a one-sentence plain-English description of this diagnosis.'
    ) as diagnosis_description
FROM X12_EDI_AI.GOLD.GOLD_CLAIMS gc;

------------------------------------------------------------------------
-- SAMPLE ANALYTICS QUERIES
------------------------------------------------------------------------

-- Claims payment summary
-- SELECT payment_status, COUNT(*) as claim_count, SUM(claim_amount) as total_billed, SUM(payment_amount) as total_paid
-- FROM X12_EDI_AI.GOLD.GOLD_CLAIMS GROUP BY 1;

-- AI-enriched analysis
-- SELECT claim_id, diagnosis_code_1, clinical_specialty, diagnosis_description, claim_amount
-- FROM X12_EDI_AI.GOLD.GOLD_CLAIMS_AI_ENRICHED LIMIT 10;

-- Underpayment analysis
-- SELECT claim_id, claim_amount, payment_amount, underpayment_amount, adjustment_group_code
-- FROM X12_EDI_AI.GOLD.GOLD_CLAIMS WHERE payment_status = 'PAID' ORDER BY underpayment_amount DESC;
