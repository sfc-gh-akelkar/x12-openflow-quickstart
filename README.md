# x12-to-insights

**From 300MB EDI Files to AI-Enriched Claims in 15 Minutes.**

A production-grade pipeline for ingesting HIPAA X12 EDI healthcare transactions (837P Professional Claims) from S3 into Snowflake using Openflow, Snowpipe Streaming, Dynamic Tables, and Cortex AI.

```
S3 (300MB files)
  → Openflow (split, extract, stream)
    → Bronze: raw transactions (Snowpipe Streaming, no warehouse)
      → Silver: parsed segments (Dynamic Tables, auto-refresh)
        → Gold: analytics-ready claims + AI enrichment (Claude Sonnet 4-6)
```

---

## Quick Start

### Prerequisites

- Snowflake account with ACCOUNTADMIN access
- Openflow (Snowpark Container Services) enabled
- S3 bucket (any region)
- RSA key pair (PKCS8, unencrypted) for Snowpipe Streaming auth
- Cortex AI access (`AI_COMPLETE` function)

### Step 1: Run Prerequisites SQL

```bash
# In Snowflake worksheet or CLI:
sql/00_prerequisites.sql
```

This creates the warehouse, database, schemas, and validates your Cortex AI access.

### Step 2: Upload Sample Data to S3

```bash
aws s3 cp data/sample_837p_20_claims.edi s3://<your-bucket>/x12/
```

### Step 3: Set Up Openflow (Build the Flow)

Create an Openflow deployment and runtime, then build this 6-processor flow manually:

#### Processor 1: ListS3
| Property | Value |
|----------|-------|
| Bucket | `<your-bucket>` |
| Prefix | `x12/` |
| Region | `us-west-2` (or your region) |
| Listing Strategy | `Tracking Timestamps` |

#### Processor 2: FetchS3Object
| Property | Value |
|----------|-------|
| Bucket | Same as ListS3 |
| Region | Same as ListS3 |

#### Processor 3: SplitContent
| Property | Value |
|----------|-------|
| Byte Sequence | `ST*` |
| Keep Byte Sequence | `Leading` |

This splits a multi-hundred-MB file into individual X12 transactions at the `ST*` transaction set boundary.

#### Processor 4: ExtractText
| Property | Value |
|----------|-------|
| Dynamic Property Name | `x12_content` |
| Dynamic Property Value | `([\s\S]+)` |

Captures the full transaction content as a FlowFile attribute.

#### Processor 5: ReplaceText
| Property | Value |
|----------|-------|
| Replacement Strategy | `Always Replace` |
| Evaluation Mode | `Entire text` |
| Replacement Value | `{"RAW_X12_DATA":"${x12_content:escapeJson()}","SOURCE_SYSTEM":"OPENFLOW_S3","MESSAGE_ID":"${UUID()}","INGESTION_TIMESTAMP":${now():toNumber()}}` |

Wraps raw X12 text into a JSON record with a UUID and epoch timestamp.

#### Processor 6: PutSnowpipeStreaming (v1)
| Property | Value |
|----------|-------|
| Account | Your account locator (e.g., `RRB23678`) |
| User | Your Snowflake username |
| Role | `ACCOUNTADMIN` |
| Authentication | `Key Pair` |
| Private Key Service | `StandardPrivateKeyService` (paste PKCS8 private key) |
| Database | `X12_EDI_AI` |
| Schema | `STAGING` |
| Table | `LANDING_X12_RAW` |
| Record Reader | `JsonTreeReader` |
| Delivery Guarantee | `At least once` |
| Client Lag | `1 sec` |

> **Important:** Use PutSnowpipeStreaming (v1), NOT PutSnowpipeStreaming2. v1 uses a Record Reader + Table target. v2 uses NDJSON + Pipe + Offset Tokens — wrong for this pattern.

#### Controller Services

- **JsonTreeReader** — default settings
- **StandardPrivateKeyService** — paste your RSA private key (PKCS8, unencrypted, including `-----BEGIN PRIVATE KEY-----` header)
- **AWSCredentialsProviderControllerService** — Access Key + Secret Key for S3

#### Connections

- Auto-terminate `failure` on: ReplaceText, PutSnowpipeStreaming
- Auto-terminate `success` on: PutSnowpipeStreaming
- Auto-terminate `original` on: SplitContent

### Step 4: Create the Pipeline Tables

```bash
# In Snowflake worksheet or CLI:
sql/01_x12_pipeline.sql
```

This creates:
- **Bronze:** `STAGING.LANDING_X12_RAW` (landing table)
- **Silver:** 6 Dynamic Tables that parse X12 segments
- **Gold:** 2 Dynamic Tables (unified claims + AI-enriched)

### Step 5: Start the Flow

Start all processors in Openflow. Data begins streaming within seconds.

### Step 6: Verify

```sql
-- Check Bronze
SELECT COUNT(*) FROM X12_EDI_AI.STAGING.LANDING_X12_RAW;

-- Check Gold (wait 10-15 min for Dynamic Tables to refresh)
SELECT * FROM X12_EDI_AI.GOLD.GOLD_CLAIMS_AI_ENRICHED LIMIT 10;
```

---

## Volume Testing

Generate large files for load testing:

```bash
# 500K claims (~300MB)
python scripts/generate_x12_claims.py --claims 500000 --output volume_837p_500k.edi

# Upload to S3
aws s3 cp volume_837p_500k.edi s3://<your-bucket>/x12/
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "does not support columns with a default value" | Landing table has DEFAULT or IDENTITY columns | Use plain VARCHAR columns, generate values in ReplaceText |
| "IP X.X.X.X is not allowed" | SPCS container IP blocked by network policy | Add a /24 CIDR block to your network policy |
| "Value cannot be ingested into column of type TIMESTAMP" | Snowpipe Streaming rejects the timestamp format | Make the column VARCHAR, cast to TIMESTAMP in Dynamic Tables |
| Queue 100% full in Openflow | PutSnowpipeStreaming slower than upstream | Increase Concurrent Tasks to 3-4 on PutSnowpipeStreaming |

---

## Repo Structure

```
x12-to-insights/
├── README.md                          ← You are here
├── sql/
│   ├── 00_prerequisites.sql           ← Run first: warehouse, schemas, key-pair
│   └── 01_x12_pipeline.sql           ← Bronze table + all Dynamic Tables
├── data/
│   └── sample_837p_20_claims.edi      ← 20 test claims, upload to S3
├── scripts/
│   └── generate_x12_claims.py         ← Generate volume test files
└── docs/
    └── blog_x12_openflow_pipeline.html ← Full blog post (open in browser)
```

---

## Architecture

| Layer | Table | What It Does |
|-------|-------|-------------|
| Bronze | `STAGING.LANDING_X12_RAW` | Raw X12 transactions as-is from Openflow |
| Silver | `SILVER.SILVER_X12_SEGMENTS` | Explodes each transaction into ~25 segment rows |
| Silver | `SILVER.SILVER_CLAIMS_HEADER` | Extracts CLM fields: claim ID, billed amount |
| Silver | `SILVER.SILVER_PATIENTS` | Extracts NM1*IL + DMG: patient name, DOB, gender |
| Silver | `SILVER.SILVER_PROVIDERS` | Extracts NM1*85/82: billing/rendering provider, NPI |
| Silver | `SILVER.SILVER_DIAGNOSES` | Extracts HI: ICD-10 diagnosis code |
| Silver | `SILVER.SILVER_SERVICE_LINES` | Extracts SV1: procedure code, charge, units |
| Gold | `GOLD.GOLD_CLAIMS_COMPLETE` | Joins all Silver tables into one record per claim |
| Gold | `GOLD.GOLD_CLAIMS_AI_ENRICHED` | Adds AI-decoded diagnosis (description, category, chronic flag) |

---

## License

Apache 2.0
