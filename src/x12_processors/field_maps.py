FIELD_MAPS = {
    "834": {
        "transaction_type_name": "Benefit Enrollment and Maintenance",
        "record_boundary_segment": "INS",
        "fields": {
            "INS": {
                "01": "benefit_status",
                "02": "individual_relationship_code",
                "03": "maintenance_type_code",
                "04": "maintenance_reason_code",
                "05": "benefit_status_code",
                "08": "employment_status_code",
            },
            "REF": {
                "02": "reference_id",
            },
            "DTP_336": {
                "03": "employment_date",
            },
            "DTP_348": {
                "03": "coverage_start_date",
            },
            "DTP_349": {
                "03": "coverage_end_date",
            },
            "DTP_303": {
                "03": "maintenance_effective_date",
            },
            "NM1_IL": {
                "02": "member_entity_type",
                "03": "member_last_name",
                "04": "member_first_name",
                "05": "member_middle_name",
                "06": "member_name_prefix",
                "07": "member_name_suffix",
                "08": "member_id_qualifier",
                "09": "member_id",
            },
            "NM1_70": {
                "03": "prior_last_name",
                "04": "prior_first_name",
                "09": "prior_id",
            },
            "N3": {
                "01": "member_address_line_1",
                "02": "member_address_line_2",
            },
            "N4": {
                "01": "member_city",
                "02": "member_state",
                "03": "member_zip",
                "04": "member_country",
            },
            "DMG": {
                "02": "member_dob",
                "03": "member_gender",
                "04": "member_marital_status",
            },
            "HD": {
                "01": "maintenance_type",
                "03": "insurance_line_code",
                "04": "plan_coverage_description",
                "05": "coverage_level_code",
            },
            "ICM": {
                "01": "frequency_code",
                "02": "wage_amount",
                "05": "salary_grade",
            },
            "LUI": {
                "02": "language_code",
                "03": "language_description",
            },
        },
    },
    "835": {
        "transaction_type_name": "Health Care Claim Payment/Advice",
        "record_boundary_segment": "CLP",
        "fields": {
            "CLP": {
                "01": "claim_id",
                "02": "claim_status_code",
                "03": "claim_charge_amount",
                "04": "claim_payment_amount",
                "05": "patient_responsibility_amount",
                "06": "claim_filing_indicator_code",
                "07": "payer_claim_control_number",
                "08": "facility_type_code",
                "09": "claim_frequency_code",
            },
            "NM1_QC": {
                "03": "patient_last_name",
                "04": "patient_first_name",
                "05": "patient_middle_name",
                "08": "patient_id_qualifier",
                "09": "patient_id",
            },
            "NM1_82": {
                "03": "rendering_provider_last_name",
                "04": "rendering_provider_first_name",
                "08": "rendering_provider_id_qualifier",
                "09": "rendering_provider_npi",
            },
            "NM1_TT": {
                "03": "crossover_payer_name",
                "09": "crossover_payer_id",
            },
            "SVC": {
                "01": "procedure_code",
                "02": "service_charge_amount",
                "03": "service_payment_amount",
                "04": "revenue_code",
                "05": "units_paid",
                "07": "original_procedure_code",
            },
            "CAS": {
                "01": "adjustment_group_code",
                "02": "adjustment_reason_code_1",
                "03": "adjustment_amount_1",
                "05": "adjustment_reason_code_2",
                "06": "adjustment_amount_2",
            },
            "DTM_232": {
                "02": "service_date",
            },
            "DTM_233": {
                "02": "service_end_date",
            },
            "DTM_036": {
                "02": "coverage_expiration_date",
            },
            "AMT_AU": {
                "02": "allowed_amount",
            },
            "AMT_D8": {
                "02": "discount_amount",
            },
        },
    },
    "837": {
        "transaction_type_name": "Health Care Claim",
        "record_boundary_segment": "CLM",
        "fields": {
            "CLM": {
                "01": "claim_id",
                "02": "claim_amount",
                "05": "place_of_service_code",
                "06": "provider_signature_indicator",
                "07": "assignment_of_benefits",
                "08": "benefits_assignment_certification",
                "09": "release_of_information_code",
            },
            "NM1_85": {
                "02": "billing_provider_entity_type",
                "03": "billing_provider_last_name",
                "04": "billing_provider_first_name",
                "08": "billing_provider_id_qualifier",
                "09": "billing_provider_npi",
            },
            "NM1_87": {
                "03": "pay_to_provider_last_name",
                "04": "pay_to_provider_first_name",
                "09": "pay_to_provider_npi",
            },
            "NM1_IL": {
                "03": "subscriber_last_name",
                "04": "subscriber_first_name",
                "05": "subscriber_middle_name",
                "08": "subscriber_id_qualifier",
                "09": "subscriber_id",
            },
            "NM1_QC": {
                "03": "patient_last_name",
                "04": "patient_first_name",
                "05": "patient_middle_name",
            },
            "NM1_DN": {
                "03": "referring_provider_last_name",
                "04": "referring_provider_first_name",
                "09": "referring_provider_npi",
            },
            "NM1_82": {
                "03": "rendering_provider_last_name",
                "04": "rendering_provider_first_name",
                "09": "rendering_provider_npi",
            },
            "N3_85": {
                "01": "billing_provider_address_1",
                "02": "billing_provider_address_2",
            },
            "N4_85": {
                "01": "billing_provider_city",
                "02": "billing_provider_state",
                "03": "billing_provider_zip",
            },
            "SBR": {
                "01": "payer_responsibility_sequence",
                "02": "individual_relationship_code",
                "03": "subscriber_group_number",
                "04": "subscriber_group_name",
                "09": "claim_filing_indicator",
            },
            "DMG": {
                "02": "patient_dob",
                "03": "patient_gender",
            },
            "DTP_431": {
                "03": "onset_date",
            },
            "DTP_472": {
                "03": "service_date",
            },
            "DTP_435": {
                "03": "admission_date",
            },
            "DTP_096": {
                "03": "discharge_date",
            },
            "HI": {
                "01": "diagnosis_code_1",
                "02": "diagnosis_code_2",
                "03": "diagnosis_code_3",
                "04": "diagnosis_code_4",
                "05": "diagnosis_code_5",
                "06": "diagnosis_code_6",
                "07": "diagnosis_code_7",
                "08": "diagnosis_code_8",
            },
            "SV1": {
                "01": "procedure_code",
                "02": "service_charge_amount",
                "03": "unit_basis",
                "04": "service_unit_count",
                "05": "place_of_service",
                "07": "diagnosis_code_pointer",
            },
            "SV2": {
                "01": "revenue_code",
                "02": "procedure_code",
                "03": "service_charge_amount",
                "04": "unit_basis",
                "05": "service_unit_count",
            },
            "REF_EA": {
                "02": "patient_account_number",
            },
            "REF_D9": {
                "02": "claim_reference_id",
            },
        },
    },
    "270": {
        "transaction_type_name": "Health Care Eligibility/Benefit Inquiry",
        "record_boundary_segment": "HL",
        "fields": {
            "HL": {
                "01": "hierarchy_id",
                "02": "hierarchy_parent_id",
                "03": "hierarchy_level_code",
                "04": "hierarchy_child_code",
            },
            "NM1_PR": {
                "03": "payer_name",
                "09": "payer_id",
            },
            "NM1_1P": {
                "03": "provider_last_name",
                "04": "provider_first_name",
                "08": "provider_id_qualifier",
                "09": "provider_npi",
            },
            "NM1_IL": {
                "03": "subscriber_last_name",
                "04": "subscriber_first_name",
                "08": "subscriber_id_qualifier",
                "09": "subscriber_id",
            },
            "NM1_03": {
                "03": "dependent_last_name",
                "04": "dependent_first_name",
            },
            "DMG": {
                "02": "subscriber_dob",
                "03": "subscriber_gender",
            },
            "DTP_291": {
                "03": "eligibility_date",
            },
            "DTP_307": {
                "03": "eligibility_date_range",
            },
            "EQ": {
                "01": "service_type_code",
                "02": "coverage_level_code",
                "03": "insurance_type_code",
            },
        },
    },
    "271": {
        "transaction_type_name": "Health Care Eligibility/Benefit Response",
        "record_boundary_segment": "HL",
        "fields": {
            "HL": {
                "01": "hierarchy_id",
                "02": "hierarchy_parent_id",
                "03": "hierarchy_level_code",
                "04": "hierarchy_child_code",
            },
            "NM1_PR": {
                "03": "payer_name",
                "09": "payer_id",
            },
            "NM1_1P": {
                "03": "provider_last_name",
                "04": "provider_first_name",
                "09": "provider_npi",
            },
            "NM1_IL": {
                "03": "subscriber_last_name",
                "04": "subscriber_first_name",
                "08": "subscriber_id_qualifier",
                "09": "subscriber_id",
            },
            "DMG": {
                "02": "subscriber_dob",
                "03": "subscriber_gender",
            },
            "EB": {
                "01": "eligibility_or_benefit_code",
                "02": "coverage_level_code",
                "03": "service_type_code",
                "04": "insurance_type_code",
                "05": "plan_coverage_description",
                "06": "time_period_qualifier",
                "07": "benefit_amount",
                "08": "benefit_percent",
                "09": "benefit_quantity_qualifier",
                "10": "benefit_quantity",
            },
            "DTP_291": {
                "03": "benefit_date",
            },
            "DTP_307": {
                "03": "benefit_date_range",
            },
            "MSG": {
                "01": "free_form_message_text",
            },
            "AAA": {
                "01": "request_validation_code",
                "03": "reject_reason_code",
                "04": "follow_up_action_code",
            },
        },
    },
    "276": {
        "transaction_type_name": "Health Care Claim Status Request",
        "record_boundary_segment": "HL",
        "fields": {
            "HL": {
                "01": "hierarchy_id",
                "02": "hierarchy_parent_id",
                "03": "hierarchy_level_code",
                "04": "hierarchy_child_code",
            },
            "NM1_PR": {
                "03": "payer_name",
                "09": "payer_id",
            },
            "NM1_41": {
                "03": "submitter_name",
                "09": "submitter_id",
            },
            "NM1_1P": {
                "03": "provider_last_name",
                "04": "provider_first_name",
                "09": "provider_npi",
            },
            "NM1_IL": {
                "03": "subscriber_last_name",
                "04": "subscriber_first_name",
                "09": "subscriber_id",
            },
            "NM1_QC": {
                "03": "patient_last_name",
                "04": "patient_first_name",
            },
            "TRN": {
                "02": "trace_number",
                "03": "trace_originating_company_id",
            },
            "REF_BLT": {
                "02": "claim_reference_id",
            },
            "AMT_T3": {
                "02": "claim_charge_amount",
            },
            "DTP_472": {
                "03": "service_date",
            },
        },
    },
    "277": {
        "transaction_type_name": "Health Care Claim Status Response",
        "record_boundary_segment": "HL",
        "fields": {
            "HL": {
                "01": "hierarchy_id",
                "02": "hierarchy_parent_id",
                "03": "hierarchy_level_code",
                "04": "hierarchy_child_code",
            },
            "NM1_PR": {
                "03": "payer_name",
                "09": "payer_id",
            },
            "NM1_1P": {
                "03": "provider_last_name",
                "04": "provider_first_name",
                "09": "provider_npi",
            },
            "NM1_IL": {
                "03": "subscriber_last_name",
                "04": "subscriber_first_name",
                "09": "subscriber_id",
            },
            "NM1_QC": {
                "03": "patient_last_name",
                "04": "patient_first_name",
            },
            "TRN": {
                "02": "trace_number",
                "03": "trace_originating_company_id",
            },
            "STC": {
                "01": "status_information_code",
                "02": "status_effective_date",
                "03": "action_code",
                "04": "claim_payment_amount",
                "10": "claim_status_code",
                "11": "entity_identifier_code",
            },
            "REF_1K": {
                "02": "payer_claim_number",
            },
            "DTP_472": {
                "03": "service_date",
            },
        },
    },
}

GS_FIC_TO_TRANSACTION = {
    "HP": "835",
    "HC": "837",
    "HI": "834",
    "HS": "270",
    "HB": "271",
    "HN": "276",
    "HU": "277",
}

ST_CODE_TO_TRANSACTION = {
    "834": "834",
    "835": "835",
    "837": "837",
    "270": "270",
    "271": "271",
    "276": "276",
    "277": "277",
}
