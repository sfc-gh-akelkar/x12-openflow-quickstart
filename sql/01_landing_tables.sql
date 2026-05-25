------------------------------------------------------------------------
-- X12 EDI Pipeline: Landing Tables
-- These tables receive structured JSON from ParseX12ToJSON via Openflow.
-- Each column matches the exact field names output by the parser.
-- ENABLE_SCHEMA_EVOLUTION handles any new fields automatically.
------------------------------------------------------------------------

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE APP_WH;

------------------------------------------------------------------------
-- 837: Professional Claims
-- Record boundary: CLM (one record per claim)
------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS X12_EDI_AI.CLAIMS.LANDING_837_CLAIMS (
    -- Envelope (ISA/GS)
    interchange_sender_id           VARCHAR,
    interchange_receiver_id         VARCHAR,
    interchange_date                VARCHAR,
    interchange_time                VARCHAR,
    interchange_control_number      VARCHAR,
    interchange_usage_indicator     VARCHAR,
    functional_id_code              VARCHAR,
    application_sender_code         VARCHAR,
    application_receiver_code       VARCHAR,
    group_date                      VARCHAR,
    group_time                      VARCHAR,
    group_control_number            VARCHAR,
    responsible_agency_code         VARCHAR,
    version_release_industry_code   VARCHAR,
    -- Transaction
    transaction_type                VARCHAR,
    transaction_set_control_number  VARCHAR,
    implementation_guide_version    VARCHAR,
    -- Claim header (CLM)
    claim_id                        VARCHAR,
    claim_amount                    VARCHAR,
    place_of_service_code           VARCHAR,
    provider_signature_indicator    VARCHAR,
    assignment_of_benefits          VARCHAR,
    benefits_assignment_certification VARCHAR,
    release_of_information_code     VARCHAR,
    -- Billing provider (NM1*85)
    billing_provider_entity_type    VARCHAR,
    billing_provider_last_name      VARCHAR,
    billing_provider_first_name     VARCHAR,
    billing_provider_id_qualifier   VARCHAR,
    billing_provider_npi            VARCHAR,
    billing_provider_address_1      VARCHAR,
    billing_provider_address_2      VARCHAR,
    billing_provider_city           VARCHAR,
    billing_provider_state          VARCHAR,
    billing_provider_zip            VARCHAR,
    -- Pay-to provider (NM1*87)
    pay_to_provider_last_name       VARCHAR,
    pay_to_provider_first_name      VARCHAR,
    pay_to_provider_npi             VARCHAR,
    -- Rendering provider (NM1*82)
    rendering_provider_last_name    VARCHAR,
    rendering_provider_first_name   VARCHAR,
    rendering_provider_npi          VARCHAR,
    -- Referring provider (NM1*DN)
    referring_provider_last_name    VARCHAR,
    referring_provider_first_name   VARCHAR,
    referring_provider_npi          VARCHAR,
    -- Subscriber (NM1*IL)
    subscriber_last_name            VARCHAR,
    subscriber_first_name           VARCHAR,
    subscriber_middle_name          VARCHAR,
    subscriber_id_qualifier         VARCHAR,
    subscriber_id                   VARCHAR,
    -- Patient (NM1*QC, DMG)
    patient_last_name               VARCHAR,
    patient_first_name              VARCHAR,
    patient_middle_name             VARCHAR,
    patient_dob                     VARCHAR,
    patient_gender                  VARCHAR,
    -- Insurance (SBR)
    payer_responsibility_sequence   VARCHAR,
    individual_relationship_code    VARCHAR,
    subscriber_group_number         VARCHAR,
    subscriber_group_name           VARCHAR,
    claim_filing_indicator          VARCHAR,
    -- Diagnosis (HI)
    diagnosis_code_1                VARCHAR,
    diagnosis_code_2                VARCHAR,
    diagnosis_code_3                VARCHAR,
    diagnosis_code_4                VARCHAR,
    diagnosis_code_5                VARCHAR,
    diagnosis_code_6                VARCHAR,
    diagnosis_code_7                VARCHAR,
    diagnosis_code_8                VARCHAR,
    -- Service line (SV1) — multi-value semicolon-separated
    procedure_code                  VARCHAR,
    service_charge_amount           VARCHAR,
    unit_basis                      VARCHAR,
    service_unit_count              VARCHAR,
    place_of_service                VARCHAR,
    diagnosis_code_pointer          VARCHAR,
    revenue_code                    VARCHAR,
    -- Dates (DTP)
    service_date                    VARCHAR,
    onset_date                      VARCHAR,
    admission_date                  VARCHAR,
    discharge_date                  VARCHAR,
    -- Reference (REF)
    patient_account_number          VARCHAR,
    claim_reference_id              VARCHAR
) ENABLE_SCHEMA_EVOLUTION = TRUE;

GRANT EVOLVE SCHEMA ON TABLE X12_EDI_AI.CLAIMS.LANDING_837_CLAIMS TO ROLE ACCOUNTADMIN;

------------------------------------------------------------------------
-- 834: Benefit Enrollment and Maintenance
-- Record boundary: INS (one record per member action)
------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS X12_EDI_AI.ENROLLMENTS.LANDING_834_ENROLLMENTS (
    -- Envelope
    interchange_sender_id           VARCHAR,
    interchange_receiver_id         VARCHAR,
    interchange_date                VARCHAR,
    interchange_time                VARCHAR,
    interchange_control_number      VARCHAR,
    interchange_usage_indicator     VARCHAR,
    functional_id_code              VARCHAR,
    application_sender_code         VARCHAR,
    application_receiver_code       VARCHAR,
    group_date                      VARCHAR,
    group_time                      VARCHAR,
    group_control_number            VARCHAR,
    responsible_agency_code         VARCHAR,
    version_release_industry_code   VARCHAR,
    -- Transaction
    transaction_type                VARCHAR,
    transaction_set_control_number  VARCHAR,
    implementation_guide_version    VARCHAR,
    -- Member action (INS)
    benefit_status                  VARCHAR,
    individual_relationship_code    VARCHAR,
    maintenance_type_code           VARCHAR,
    maintenance_reason_code         VARCHAR,
    benefit_status_code             VARCHAR,
    employment_status_code          VARCHAR,
    -- Member identity (NM1*IL)
    member_entity_type              VARCHAR,
    member_last_name                VARCHAR,
    member_first_name               VARCHAR,
    member_middle_name              VARCHAR,
    member_name_prefix              VARCHAR,
    member_name_suffix              VARCHAR,
    member_id_qualifier             VARCHAR,
    member_id                       VARCHAR,
    -- Prior name (NM1*70)
    prior_last_name                 VARCHAR,
    prior_first_name                VARCHAR,
    prior_id                        VARCHAR,
    -- Address (N3, N4)
    member_address_line_1           VARCHAR,
    member_address_line_2           VARCHAR,
    member_city                     VARCHAR,
    member_state                    VARCHAR,
    member_zip                      VARCHAR,
    member_country                  VARCHAR,
    -- Demographics (DMG)
    member_dob                      VARCHAR,
    member_gender                   VARCHAR,
    member_marital_status           VARCHAR,
    -- Coverage (HD)
    maintenance_type                VARCHAR,
    insurance_line_code             VARCHAR,
    plan_coverage_description       VARCHAR,
    coverage_level_code             VARCHAR,
    -- Dates (DTP)
    employment_date                 VARCHAR,
    coverage_start_date             VARCHAR,
    coverage_end_date               VARCHAR,
    maintenance_effective_date      VARCHAR,
    -- Reference
    reference_id                    VARCHAR,
    -- Income (ICM)
    frequency_code                  VARCHAR,
    wage_amount                     VARCHAR,
    salary_grade                    VARCHAR,
    -- Language (LUI)
    language_code                   VARCHAR,
    language_description            VARCHAR
) ENABLE_SCHEMA_EVOLUTION = TRUE;

GRANT EVOLVE SCHEMA ON TABLE X12_EDI_AI.ENROLLMENTS.LANDING_834_ENROLLMENTS TO ROLE ACCOUNTADMIN;

------------------------------------------------------------------------
-- 835: Health Care Claim Payment/Advice (Remittance)
-- Record boundary: CLP (one record per claim payment)
------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS X12_EDI_AI.REMITTANCES.LANDING_835_REMITTANCES (
    -- Envelope
    interchange_sender_id           VARCHAR,
    interchange_receiver_id         VARCHAR,
    interchange_date                VARCHAR,
    interchange_time                VARCHAR,
    interchange_control_number      VARCHAR,
    interchange_usage_indicator     VARCHAR,
    functional_id_code              VARCHAR,
    application_sender_code         VARCHAR,
    application_receiver_code       VARCHAR,
    group_date                      VARCHAR,
    group_time                      VARCHAR,
    group_control_number            VARCHAR,
    responsible_agency_code         VARCHAR,
    version_release_industry_code   VARCHAR,
    -- Transaction
    transaction_type                VARCHAR,
    transaction_set_control_number  VARCHAR,
    implementation_guide_version    VARCHAR,
    -- Claim payment (CLP)
    claim_id                        VARCHAR,
    claim_status_code               VARCHAR,
    claim_charge_amount             VARCHAR,
    claim_payment_amount            VARCHAR,
    patient_responsibility_amount   VARCHAR,
    claim_filing_indicator_code     VARCHAR,
    payer_claim_control_number      VARCHAR,
    facility_type_code              VARCHAR,
    claim_frequency_code            VARCHAR,
    -- Patient (NM1*QC)
    patient_last_name               VARCHAR,
    patient_first_name              VARCHAR,
    patient_middle_name             VARCHAR,
    patient_id_qualifier            VARCHAR,
    patient_id                      VARCHAR,
    -- Rendering provider (NM1*82)
    rendering_provider_last_name    VARCHAR,
    rendering_provider_first_name   VARCHAR,
    rendering_provider_id_qualifier VARCHAR,
    rendering_provider_npi          VARCHAR,
    -- Crossover payer (NM1*TT)
    crossover_payer_name            VARCHAR,
    crossover_payer_id              VARCHAR,
    -- Service line (SVC) — multi-value semicolon-separated
    procedure_code                  VARCHAR,
    service_charge_amount           VARCHAR,
    service_payment_amount          VARCHAR,
    revenue_code                    VARCHAR,
    units_paid                      VARCHAR,
    original_procedure_code         VARCHAR,
    -- Adjustments (CAS)
    adjustment_group_code           VARCHAR,
    adjustment_reason_code_1        VARCHAR,
    adjustment_amount_1             VARCHAR,
    adjustment_reason_code_2        VARCHAR,
    adjustment_amount_2             VARCHAR,
    -- Dates (DTM)
    service_date                    VARCHAR,
    service_end_date                VARCHAR,
    coverage_expiration_date        VARCHAR,
    -- Amounts (AMT)
    allowed_amount                  VARCHAR,
    discount_amount                 VARCHAR
) ENABLE_SCHEMA_EVOLUTION = TRUE;

GRANT EVOLVE SCHEMA ON TABLE X12_EDI_AI.REMITTANCES.LANDING_835_REMITTANCES TO ROLE ACCOUNTADMIN;
