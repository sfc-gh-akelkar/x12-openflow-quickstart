------------------------------------------------------------------------
-- X12 EDI Pipeline: Landing Tables (Production)
-- These tables receive structured JSON from ParseX12ToJSON via Openflow.
-- Each table matches the exact field names output by the parser.
-- No parsing happens in Snowflake — data arrives structured.
------------------------------------------------------------------------

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE APP_WH;

CREATE DATABASE IF NOT EXISTS X12_EDI_AI;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.CLAIMS;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.ENROLLMENTS;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.REMITTANCES;

------------------------------------------------------------------------
-- 837: Professional Claims
-- Record boundary: CLM (one record per claim)
------------------------------------------------------------------------
CREATE OR REPLACE TABLE X12_EDI_AI.CLAIMS.LANDING_837_CLAIMS (
    -- Envelope (from ISA/GS when Include Envelope = true)
    transaction_type                VARCHAR(10),
    transaction_set_control_number  VARCHAR(20),
    implementation_guide_version    VARCHAR(30),
    interchange_sender_id           VARCHAR(15),
    interchange_receiver_id         VARCHAR(15),
    interchange_date                VARCHAR(8),
    interchange_control_number      VARCHAR(15),
    functional_id_code              VARCHAR(5),
    application_sender_code         VARCHAR(15),
    application_receiver_code       VARCHAR(15),
    group_control_number            VARCHAR(15),
    version_release_industry_code   VARCHAR(15),

    -- Claim header (CLM segment)
    claim_id                        VARCHAR(50),
    claim_amount                    VARCHAR(20),
    place_of_service_code           VARCHAR(10),
    provider_signature_indicator    VARCHAR(5),
    assignment_of_benefits          VARCHAR(5),
    release_of_information_code     VARCHAR(5),

    -- Billing provider (NM1*85)
    billing_provider_entity_type    VARCHAR(5),
    billing_provider_last_name      VARCHAR(100),
    billing_provider_first_name     VARCHAR(50),
    billing_provider_id_qualifier   VARCHAR(5),
    billing_provider_npi            VARCHAR(20),

    -- Rendering provider (NM1*82)
    rendering_provider_last_name    VARCHAR(100),
    rendering_provider_first_name   VARCHAR(50),
    rendering_provider_npi          VARCHAR(20),

    -- Referring provider (NM1*DN)
    referring_provider_last_name    VARCHAR(100),
    referring_provider_first_name   VARCHAR(50),
    referring_provider_npi          VARCHAR(20),

    -- Subscriber/Patient (NM1*IL, DMG)
    subscriber_last_name            VARCHAR(100),
    subscriber_first_name           VARCHAR(50),
    subscriber_middle_name          VARCHAR(50),
    subscriber_id_qualifier         VARCHAR(5),
    subscriber_id                   VARCHAR(50),
    patient_dob                     VARCHAR(10),
    patient_gender                  VARCHAR(5),

    -- Insurance (SBR)
    payer_responsibility_sequence   VARCHAR(5),
    individual_relationship_code    VARCHAR(5),
    subscriber_group_number         VARCHAR(50),
    subscriber_group_name           VARCHAR(100),
    claim_filing_indicator          VARCHAR(10),

    -- Diagnosis (HI segment)
    diagnosis_code_1                VARCHAR(20),
    diagnosis_code_2                VARCHAR(20),
    diagnosis_code_3                VARCHAR(20),
    diagnosis_code_4                VARCHAR(20),
    diagnosis_code_5                VARCHAR(20),

    -- Service line (SV1 — last line wins, or array)
    procedure_code                  VARCHAR(20),
    service_charge_amount           VARCHAR(20),
    unit_basis                      VARCHAR(5),
    service_unit_count              VARCHAR(10),
    diagnosis_code_pointer          VARCHAR(10),

    -- Dates (DTP)
    service_date                    VARCHAR(10),
    onset_date                      VARCHAR(10),
    admission_date                  VARCHAR(10),
    discharge_date                  VARCHAR(10),

    -- Reference (REF)
    patient_account_number          VARCHAR(50)
);

------------------------------------------------------------------------
-- 834: Benefit Enrollment and Maintenance
-- Record boundary: INS (one record per member action)
------------------------------------------------------------------------
CREATE OR REPLACE TABLE X12_EDI_AI.ENROLLMENTS.LANDING_834_ENROLLMENTS (
    -- Envelope
    transaction_type                VARCHAR(10),
    transaction_set_control_number  VARCHAR(20),
    interchange_sender_id           VARCHAR(15),
    interchange_receiver_id         VARCHAR(15),
    interchange_date                VARCHAR(8),
    interchange_control_number      VARCHAR(15),
    functional_id_code              VARCHAR(5),
    application_sender_code         VARCHAR(15),
    application_receiver_code       VARCHAR(15),
    group_control_number            VARCHAR(15),

    -- Member action (INS segment)
    benefit_status                  VARCHAR(5),
    individual_relationship_code    VARCHAR(5),
    maintenance_type_code           VARCHAR(5),
    maintenance_reason_code         VARCHAR(10),
    benefit_status_code             VARCHAR(5),
    employment_status_code          VARCHAR(5),

    -- Member identity (NM1*IL)
    member_entity_type              VARCHAR(5),
    member_last_name                VARCHAR(100),
    member_first_name               VARCHAR(50),
    member_middle_name              VARCHAR(50),
    member_name_prefix              VARCHAR(10),
    member_name_suffix              VARCHAR(10),
    member_id_qualifier             VARCHAR(5),
    member_id                       VARCHAR(50),

    -- Member address (N3, N4)
    member_address_line_1           VARCHAR(200),
    member_address_line_2           VARCHAR(200),
    member_city                     VARCHAR(100),
    member_state                    VARCHAR(5),
    member_zip                      VARCHAR(15),
    member_country                  VARCHAR(5),

    -- Demographics (DMG)
    member_dob                      VARCHAR(10),
    member_gender                   VARCHAR(5),
    member_marital_status           VARCHAR(5),

    -- Coverage (HD)
    maintenance_type                VARCHAR(5),
    insurance_line_code             VARCHAR(10),
    plan_coverage_description       VARCHAR(100),
    coverage_level_code             VARCHAR(5),

    -- Dates (DTP)
    employment_date                 VARCHAR(10),
    coverage_start_date             VARCHAR(10),
    coverage_end_date               VARCHAR(10),
    maintenance_effective_date      VARCHAR(10),

    -- Reference
    reference_id                    VARCHAR(50),

    -- Income (ICM)
    frequency_code                  VARCHAR(5),
    wage_amount                     VARCHAR(20),
    salary_grade                    VARCHAR(10),

    -- Language (LUI)
    language_code                   VARCHAR(10),
    language_description            VARCHAR(50)
);

------------------------------------------------------------------------
-- 835: Health Care Claim Payment/Advice (Remittance)
-- Record boundary: CLP (one record per claim payment)
------------------------------------------------------------------------
CREATE OR REPLACE TABLE X12_EDI_AI.REMITTANCES.LANDING_835_REMITTANCES (
    -- Envelope
    transaction_type                VARCHAR(10),
    transaction_set_control_number  VARCHAR(20),
    interchange_sender_id           VARCHAR(15),
    interchange_receiver_id         VARCHAR(15),
    interchange_date                VARCHAR(8),
    interchange_control_number      VARCHAR(15),
    functional_id_code              VARCHAR(5),
    application_sender_code         VARCHAR(15),
    application_receiver_code       VARCHAR(15),
    group_control_number            VARCHAR(15),

    -- Claim payment (CLP segment)
    claim_id                        VARCHAR(50),
    claim_status_code               VARCHAR(5),
    claim_charge_amount             VARCHAR(20),
    claim_payment_amount            VARCHAR(20),
    patient_responsibility_amount   VARCHAR(20),
    claim_filing_indicator_code     VARCHAR(10),
    payer_claim_control_number      VARCHAR(50),
    facility_type_code              VARCHAR(10),
    claim_frequency_code            VARCHAR(5),

    -- Patient (NM1*QC)
    patient_last_name               VARCHAR(100),
    patient_first_name              VARCHAR(50),
    patient_middle_name             VARCHAR(50),
    patient_id_qualifier            VARCHAR(5),
    patient_id                      VARCHAR(50),

    -- Rendering provider (NM1*82)
    rendering_provider_last_name    VARCHAR(100),
    rendering_provider_first_name   VARCHAR(50),
    rendering_provider_id_qualifier VARCHAR(5),
    rendering_provider_npi          VARCHAR(20),

    -- Crossover payer (NM1*TT)
    crossover_payer_name            VARCHAR(100),
    crossover_payer_id              VARCHAR(50),

    -- Service line (SVC)
    procedure_code                  VARCHAR(20),
    service_charge_amount           VARCHAR(20),
    service_payment_amount          VARCHAR(20),
    revenue_code                    VARCHAR(10),
    units_paid                      VARCHAR(10),
    original_procedure_code         VARCHAR(20),

    -- Adjustments (CAS)
    adjustment_group_code           VARCHAR(5),
    adjustment_reason_code_1        VARCHAR(10),
    adjustment_amount_1             VARCHAR(20),
    adjustment_reason_code_2        VARCHAR(10),
    adjustment_amount_2             VARCHAR(20),

    -- Dates (DTM)
    service_date                    VARCHAR(10),
    service_end_date                VARCHAR(10),
    coverage_expiration_date        VARCHAR(10),

    -- Amounts (AMT)
    allowed_amount                  VARCHAR(20),
    discount_amount                 VARCHAR(20)
);
