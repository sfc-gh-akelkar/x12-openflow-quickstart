# Building a Real-Time HIPAA X12 EDI Pipeline with Openflow and Cortex AI

## Overview

This guide shows you how to build a production-grade streaming pipeline that ingests HIPAA X12 EDI files from S3, parses them into structured records, loads them into Snowflake via Snowpipe Streaming, and enriches them with Cortex AI — all using Openflow's visual workflow builder.

### What You Will Build

- A custom Python processor (ParseX12ToJSON) that transforms raw X12 EDI into structured JSON
- An Openflow canvas that routes 834/835/837 transactions into separate Snowflake tables
- Gold-layer Dynamic Tables that join claims with remittances and compute payment analytics
- AI-enriched views that classify diagnosis codes by clinical specialty using Cortex AI

### What You Will Learn

- How to build and package custom Python processors for Openflow (NAR files)
- How to configure PutSnowpipeStreaming with key-pair authentication
- How to handle X12 EDI delimiters, composite sub-elements, and multi-value fields
- How to use Dynamic Tables and Cortex AI for downstream enrichment

### Prerequisites

- Snowflake account with ACCOUNTADMIN access
- Openflow configured with a Deployment and Runtime
- S3 bucket with IAM access credentials
- RSA key pair (PKCS8, unencrypted) set on your Snowflake user
- Network policy allowing Openflow SPCS container IPs
- Python 3.9+ with `hatch` and `hatch-datavolo-nar` (for building from source)

---

## Step 1: Run the SQL Setup

Open a Snowflake worksheet and run the prerequisite scripts to create the database, schemas, and landing tables.

### 1.1 Create Database and Schemas

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS X12_EDI_AI;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.CLAIMS;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.ENROLLMENTS;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.REMITTANCES;
CREATE SCHEMA IF NOT EXISTS X12_EDI_AI.GOLD;
```

### 1.2 Create Landing Tables

Each table has columns matching the exact field names output by the ParseX12ToJSON processor. PutSnowpipeStreaming requires strict column matching — every JSON field must have a corresponding table column.

Run `sql/01_landing_tables.sql` from the repository. This creates:

| Table | Transaction Type | Record Boundary | Columns |
|-------|-----------------|-----------------|---------|
| `CLAIMS.LANDING_837_CLAIMS` | Professional Claims | CLM segment | 79 |
| `ENROLLMENTS.LANDING_834_ENROLLMENTS` | Benefit Enrollment | INS segment | 57 |
| `REMITTANCES.LANDING_835_REMITTANCES` | Claim Payment | CLP segment | 53 |

All tables have `ENABLE_SCHEMA_EVOLUTION = TRUE` as a safety net for future field additions.

### 1.3 Verify Cortex AI Access

```sql
SELECT AI_COMPLETE('claude-sonnet-4-6', 'Say hello') AS test;
```

---

## Step 2: Upload the Custom Processor to Openflow

### 2.1 Get the NAR File

**Quick option:** Download `x12_processors-0.6.0.nar` from the repository root.

**Build from source** (for customization):
```bash
pip install hatch hatch-datavolo-nar
hatch build --target nar
# Output: dist/x12_processors-<version>.nar
```

### 2.2 Upload to Openflow

1. Navigate to your Openflow Runtime
2. Go to **Extensions** (puzzle piece icon in the top-right)
3. Click **Upload NAR**
4. Select `x12_processors-0.6.0.nar`

<!-- Screenshot: screenshots/nar_upload_success.png -->
<!-- TODO: Add screenshot -->

You should see a green checkmark with "Installed" status.

### 2.3 Verify the Processor

1. Drag a new Processor onto the canvas
2. Search for "ParseX12ToJSON"
3. You should see it with tags: `x12, edi, hipaa, healthcare, parse, json, 834, 835, 837`

<!-- Screenshot: screenshots/processor_palette.png -->
<!-- TODO: Add screenshot -->

> **Troubleshooting:** If the processor shows "Invalid" with an empty Properties tab, the Python import failed. Ensure the NAR was built with `hatch-datavolo-nar` (not manually zipped) and uses the try/except import pattern.

---

## Step 3: Configure the Openflow Canvas

We'll build the pipeline left-to-right:

```
ListS3 → FetchS3 → SplitContent → ParseX12ToJSON → SplitRecord → RouteOnAttribute → PutSnowpipeStreaming (×3)
```

> **Quick start:** Import `openflow/Openflow-X12-Flow.json` into your Openflow Runtime to get the entire canvas pre-configured. You'll only need to update the AWS credentials and Snowflake connection settings.

### 3.1 ListS3

Drag a **ListS3** processor onto the canvas and configure:

| Property | Value |
|----------|-------|
| Bucket | `your-bucket-name` |
| Prefix | `x12/` |
| Region | `us-west-2` (your region) |
| AWS Credentials Provider | AWSCredentialsProviderControllerService |
| Listing Strategy | Tracking Timestamps |

> **Important:** Upload `.edi` files flat under your prefix — no subfolders. ListS3 picks up S3 "directory" marker objects (0-byte files) which will cause parse errors downstream.

### 3.2 FetchS3Object

Drag a **FetchS3Object** processor and connect ListS3 → FetchS3 (relationship: `success`).

| Property | Value |
|----------|-------|
| Bucket | Same as ListS3 |
| Region | Same as ListS3 |
| AWS Credentials Provider | Same service |

### 3.3 SplitContent

Connect FetchS3 → SplitContent (relationship: `success`).

This splits large EDI files at transaction set boundaries so ParseX12ToJSON processes one transaction at a time — essential for files with 100K+ records.

| Property | Value |
|----------|-------|
| Byte Sequence Format | Text |
| Byte Sequence | `ST*` |
| Keep Byte Sequence | `true` |
| Byte Sequence Location | Leading |

**Relationships:**
- `splits` → connect to ParseX12ToJSON
- `original` → auto-terminate

> **Note:** SplitContent strips the ISA/GS envelope from subsequent chunks. ParseX12ToJSON v0.6.0 handles this gracefully by falling back to standard X12 delimiters (`*`, `:`, `~`) when ISA is not present.

### 3.4 ParseX12ToJSON

Connect SplitContent → ParseX12ToJSON (relationship: `splits`).

| Property | Value |
|----------|-------|
| Output Mode | `ndjson` |
| Include Envelope | `true` |
| Include Raw Segments | `false` |
| Transaction Type Filter | *(leave empty)* |

**Relationships:**
- `success` → connect to SplitRecord
- `failure` → auto-terminate (catches 0-byte files gracefully)
- `original` → auto-terminate

### 3.5 SplitRecord

Connect ParseX12ToJSON → SplitRecord (relationship: `success`).

This processor splits the NDJSON output (multiple records per transaction) into individual FlowFiles (one record per FlowFile).

| Property | Value |
|----------|-------|
| Record Reader | JsonTreeReader |
| Record Writer | JsonRecordSetWriter |
| Records Per Split | `1` |

**Relationships:**
- `splits` → connect to RouteOnAttribute
- `original` → auto-terminate
- `failure` → auto-terminate

<!-- Screenshot: screenshots/splitrecord_connection.png -->
<!-- TODO: Add screenshot -->

### 3.6 RouteOnAttribute

Connect SplitRecord → RouteOnAttribute (relationship: `splits`).

This routes records by transaction type to the appropriate PutSnowpipeStreaming processor.

Add three **dynamic properties** (click the `+` button):

| Property Name | Value |
|---------------|-------|
| `claims` | `${x12.transaction.types:contains('837')}` |
| `enrollments` | `${x12.transaction.types:contains('834')}` |
| `remittances` | `${x12.transaction.types:contains('835')}` |

**Relationships:**
- `claims` → connect to PutSnowpipeStreaming (Claims)
- `enrollments` → connect to PutSnowpipeStreaming (Enrollments)
- `remittances` → connect to PutSnowpipeStreaming (Remittances)
- `unmatched` → auto-terminate

<!-- Screenshot: screenshots/routeonattribute_properties.png -->
<!-- TODO: Add screenshot -->

### 3.7 PutSnowpipeStreaming (×3)

Create three PutSnowpipeStreaming processors, one for each transaction type.

#### Controller Service: StandardPrivateKeyService

Before configuring the processors, create this controller service:

1. Go to Controller Services (gear icon)
2. Add **StandardPrivateKeyService**
3. Paste your RSA private key (full PEM including `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----`)
4. Leave Passphrase empty
5. Enable the service

#### Common Configuration (all three)

| Property | Value |
|----------|-------|
| Account | `organization-account` (e.g., `sfsenorthamerica-demo_akelkar`) |
| User | Your Snowflake username |
| Role | `ACCOUNTADMIN` |
| Authentication Strategy | Key Pair |
| Private Key Service | StandardPrivateKeyService |
| Record Reader | JsonTreeReader |
| Database | `X12_EDI_AI` |

#### Per-Instance Configuration

| Instance | Schema | Table |
|----------|--------|-------|
| Claims | `CLAIMS` | `LANDING_837_CLAIMS` |
| Enrollments | `ENROLLMENTS` | `LANDING_834_ENROLLMENTS` |
| Remittances | `REMITTANCES` | `LANDING_835_REMITTANCES` |

<!-- Screenshot: screenshots/putsnowpipestreaming_config.png -->
<!-- TODO: Add screenshot -->

> **Troubleshooting — "Authorization failed after retry":** Your network policy may be blocking the Openflow runtime's SPCS IPs. Check `LOGIN_HISTORY` for `INCOMING_REQUEST_BLOCKED` entries and add those IPs to your network policy's allowed list.

---

## Step 4: Upload Test Data to S3

Upload the sample EDI files to your S3 bucket:

```bash
aws s3 cp data/sample_837p_20_claims.edi s3://your-bucket/x12/
aws s3 cp data/sample_834_10_enrollments.edi s3://your-bucket/x12/
aws s3 cp data/sample_835_10_remittances.edi s3://your-bucket/x12/
```

<!-- Screenshot: screenshots/s3_bucket_files.png -->
<!-- TODO: Add screenshot -->

Your bucket should show three files directly under the `x12/` prefix — no subfolders.

---

## Step 5: Start the Pipeline

1. Start all processors **except** ListS3 (start from the bottom up: PutSnowpipeStreaming → RouteOnAttribute → SplitRecord → ParseX12ToJSON → SplitContent → FetchS3)
2. Start ListS3 last

The pipeline will:
- List the files in S3
- Fetch each file's content
- Split at transaction boundaries (ST*)
- Parse each transaction into structured JSON
- Split into individual records
- Route by transaction type
- Stream into Snowflake tables

---

## Step 6: Verify the Data

Go to a Snowflake worksheet:

```sql
USE ROLE ACCOUNTADMIN;

-- Check record counts
SELECT 'CLAIMS' as table_name, COUNT(*) as records FROM X12_EDI_AI.CLAIMS.LANDING_837_CLAIMS
UNION ALL
SELECT 'ENROLLMENTS', COUNT(*) FROM X12_EDI_AI.ENROLLMENTS.LANDING_834_ENROLLMENTS
UNION ALL
SELECT 'REMITTANCES', COUNT(*) FROM X12_EDI_AI.REMITTANCES.LANDING_835_REMITTANCES;
```

**Expected result:**

| TABLE_NAME | RECORDS |
|------------|---------|
| CLAIMS | 20 |
| ENROLLMENTS | 10 |
| REMITTANCES | 10 |

Sample the claims data:

```sql
SELECT claim_id, claim_amount, diagnosis_code_1, procedure_code, subscriber_last_name
FROM X12_EDI_AI.CLAIMS.LANDING_837_CLAIMS LIMIT 5;
```

You should see real ICD-10 codes (e.g., `R10.9`, `E11.9`, `J06.9`) and properly parsed field values.

---

## Step 7: Create the Gold Layer

Run `sql/02_gold_layer.sql` to create Dynamic Tables that automatically refresh as new data arrives:

```sql
-- Claims joined with remittance payments
CREATE OR REPLACE DYNAMIC TABLE X12_EDI_AI.GOLD.GOLD_CLAIMS
    TARGET_LAG = '1 minute'
    WAREHOUSE = APP_WH
AS
SELECT
    c.claim_id,
    TRY_TO_DOUBLE(c.claim_amount) as claim_amount,
    c.diagnosis_code_1,
    c.subscriber_last_name,
    TRY_TO_DOUBLE(r.claim_payment_amount) as payment_amount,
    COALESCE(TRY_TO_DOUBLE(c.claim_amount), 0)
      - COALESCE(TRY_TO_DOUBLE(r.claim_payment_amount), 0) as underpayment_amount,
    CASE WHEN r.claim_id IS NOT NULL THEN 'PAID' ELSE 'PENDING' END as payment_status
FROM X12_EDI_AI.CLAIMS.LANDING_837_CLAIMS c
LEFT JOIN X12_EDI_AI.REMITTANCES.LANDING_835_REMITTANCES r ON c.claim_id = r.claim_id;
```

Query the Gold layer:

```sql
SELECT claim_id, claim_amount, payment_amount, underpayment_amount, payment_status, diagnosis_code_1
FROM X12_EDI_AI.GOLD.GOLD_CLAIMS
ORDER BY underpayment_amount DESC LIMIT 10;
```

---

## Step 8: Add Cortex AI Enrichment

Create a view that uses Cortex AI to classify each claim by clinical specialty:

```sql
CREATE OR REPLACE VIEW X12_EDI_AI.GOLD.GOLD_CLAIMS_AI_ENRICHED AS
SELECT
    gc.*,
    AI_COMPLETE('claude-sonnet-4-6',
        'Given ICD-10 diagnosis code "' || gc.diagnosis_code_1
        || '", respond with ONLY the medical specialty name. One or two words max.'
    ) as clinical_specialty,
    AI_COMPLETE('claude-sonnet-4-6',
        'Given ICD-10 code "' || gc.diagnosis_code_1
        || '", provide a one-sentence plain-English description of this diagnosis.'
    ) as diagnosis_description
FROM X12_EDI_AI.GOLD.GOLD_CLAIMS gc;
```

Query the AI-enriched view:

```sql
SELECT claim_id, diagnosis_code_1, clinical_specialty, diagnosis_description, claim_amount, payment_status
FROM X12_EDI_AI.GOLD.GOLD_CLAIMS_AI_ENRICHED
WHERE payment_status = 'PAID' LIMIT 5;
```

**Expected result:**

| claim_id | diagnosis_code_1 | clinical_specialty | claim_amount | payment_status |
|----------|------------------|--------------------|--------------|----------------|
| CLM00000004 | J06.9 | Otolaryngology | 385.02 | PAID |
| CLM00000003 | R10.9 | Gastroenterology | 945.25 | PAID |
| CLM00000009 | E11.9 | Endocrinology | 140.47 | PAID |

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "NAR content is missing required META-INF/MANIFEST entry" | Manual zip instead of hatch build | Use `hatch build --target nar` with `hatch-datavolo-nar` |
| Processor shows "Invalid" with empty Properties tab | Python import path fails in NiFi flat-file loading | NAR must use try/except import pattern (already in v0.6.0) |
| "ISA segment not found or too short" | SplitContent removed ISA from chunks, or 0-byte S3 objects | Use v0.6.0 (falls back to standard delimiters); upload files flat |
| "Authorization failed after retry" | Network policy blocking SPCS egress IPs | Check LOGIN_HISTORY, add IPs to network policy |
| `SchemaMismatchException: [field_name]` | Table column doesn't match JSON field name | Ensure all parser output fields have matching columns |
| `[Ljava.lang.Object;@...` in table data | JSON arrays in Record Reader | Use parser v0.6.0 (concatenates multi-values as strings) |
| Diagnosis codes showing "ABK" instead of ICD codes | Sub-element separator logic taking qualifier | Use parser v0.6.0 (extracts code after composite separator) |
| `JsonEOFException` in SplitRecord | Large file output truncated | Add SplitContent before ParseX12ToJSON to split at ST* boundaries |

---

## Conclusion and Resources

### What You Built

A complete streaming EDI pipeline:
- **Ingest:** S3 → Openflow → Snowflake (sub-second latency via Snowpipe Streaming)
- **Parse:** Custom Python processor handles X12 delimiter detection, qualifier routing, and field naming
- **Route:** Transaction-type-based routing to typed landing tables
- **Enrich:** Dynamic Tables + Cortex AI for analytics-ready data

### Volume Test Results

This pipeline was tested with 1 million records:

| File | Records | Size | Result |
|------|---------|------|--------|
| `volume_837p_500k.edi` | 500,000 claims | 348 MB | 500,040 rows landed |
| `volume_834_250k.edi` | 250,000 enrollments | 73 MB | 250,019 rows landed |
| `volume_835_250k.edi` | 250,000 remittances | 97 MB | 250,020 rows landed |

Generate your own volume test files:
```bash
python scripts/generate_x12_claims.py --claims 500000 --output data/volume_837p_500k.edi
python scripts/generate_x12_enrollments.py --records 250000 --output data/volume_834_250k.edi
python scripts/generate_x12_remittances.py --records 250000 --output data/volume_835_250k.edi
```

### Production Considerations

- **Scaling:** SplitContent fans out large files into individual transactions; Openflow auto-scales with concurrent tasks; PutSnowpipeStreaming supports multiple channels per table
- **Schema changes:** If you add new fields to `field_maps.py`, you must also `ALTER TABLE ADD COLUMN` on the corresponding landing table — PutSnowpipeStreaming requires all JSON fields to have pre-existing columns
- **Monitoring:** Openflow bulletins + Snowflake LOGIN_HISTORY for end-to-end observability
- **Cost:** Dynamic Tables with 1-minute lag use warehouse credits only during refresh

### Next Steps

- Add 270/271 (eligibility) and 276/277 (claim status) transaction types
- Build a Streamlit dashboard for claims analytics
- Create a Cortex Agent for natural-language queries over EDI data
- Add alerting on denied claims or enrollment anomalies

### Resources

- [Openflow Documentation](https://docs.snowflake.com/en/user-guide/data-integration/openflow/about)
- [PutSnowpipeStreaming Processor Reference](https://docs.snowflake.com/en/user-guide/data-integration/openflow/processors/putsnowpipestreaming)
- [Snowpipe Streaming Table Support](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-table-support)
- [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-intro)
- [Cortex AI Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-llm-functions)
- [GitHub Repository](https://github.com/sfc-gh-akelkar/x12-openflow-quickstart)
