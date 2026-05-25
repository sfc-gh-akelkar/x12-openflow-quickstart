# x12-openflow-quickstart

**Production-grade X12 EDI ingestion with Openflow + Snowflake.**

Ingest HIPAA X12 healthcare transactions (837 Claims, 834 Enrollments, 835 Remittances) from S3 into Snowflake — parsed in-flight by a custom NiFi Python processor, routed by transaction type, landed as structured columns, and AI-enriched with Claude Sonnet.

```
S3 (300MB files)
  → Openflow: SplitContent → ParseX12ToJSON → RouteOnAttribute
    → 837 → PutSnowpipeStreaming → CLAIMS.LANDING_837_CLAIMS
    → 834 → PutSnowpipeStreaming → ENROLLMENTS.LANDING_834_ENROLLMENTS
    → 835 → PutSnowpipeStreaming → REMITTANCES.LANDING_835_REMITTANCES
      → Gold Dynamic Tables (AI enrichment, type casting)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  S3 BUCKET                                                           │
│  300-400MB X12 files (mixed 834/835/837)                             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OPENFLOW (Apache NiFi on SPCS)                                      │
│                                                                       │
│  ListS3 → FetchS3 → SplitContent(ST*) → ParseX12ToJSON              │
│                                              │                        │
│                                    RouteOnAttribute                   │
│                              (x12.transaction.types)                  │
│                           ┌──────────┼──────────┐                    │
│                           ↓          ↓          ↓                    │
│                         837        834        835                    │
│                           ↓          ↓          ↓                    │
│                  PutSnowpipe  PutSnowpipe  PutSnowpipe               │
│                  (CLAIMS)    (ENROLLMENTS)(REMITTANCES)               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ Snowpipe Streaming (no warehouse)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LANDING TABLES (typed columns, no parsing needed)                   │
│  • CLAIMS.LANDING_837_CLAIMS                                         │
│  • ENROLLMENTS.LANDING_834_ENROLLMENTS                               │
│  • REMITTANCES.LANDING_835_REMITTANCES                               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ Dynamic Tables (10 min lag)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  GOLD LAYER                                                          │
│  • GOLD_CLAIMS (+ AI diagnosis enrichment via Claude Sonnet 4-6)     │
│  • GOLD_ENROLLMENTS (typed dates, filtered)                          │
│  • GOLD_REMITTANCES (payment variance analysis)                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Design

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Parsing | In-flight (ParseX12ToJSON) | Handles delimiter detection, qualifier routing, field naming — once, correctly |
| Routing | RouteOnAttribute in Openflow | Each transaction type lands in its own typed table |
| Landing | Typed VARCHAR columns | No VARIANT re-extraction, no SQL parsing, direct query |
| Gold | Dynamic Tables | Only type casting + AI enrichment — no transformation logic |
| AI | Claude Sonnet 4-6 | Decodes ICD-10 codes into human-readable descriptions |

---

## Prerequisites

- [ ] Snowflake account with ACCOUNTADMIN access
- [ ] Openflow enabled (Snowpark Container Services)
- [ ] S3 bucket with X12 files
- [ ] RSA key pair (PKCS8, unencrypted) for Snowpipe Streaming
- [ ] Network policy allowing SPCS container IPs (/24 CIDR block)
- [ ] Cortex AI access (`AI_COMPLETE` function)

---

## Step 1: Run SQL Setup

```sql
-- Create landing tables (run once)
@sql/00_prerequisites.sql
@sql/01_landing_tables.sql

-- Create Gold layer (run once)
@sql/02_gold_layer.sql
```

---

## Step 2: Deploy ParseX12ToJSON to Openflow

The custom Python processor lives in `src/x12_processors/`. Deploy it as an Openflow extension:

1. In your Openflow deployment, navigate to **Extensions**
2. Upload the `src/x12_processors/` directory as a Python processor package
3. The processor `ParseX12ToJSON` will appear in the processor palette

> The processor has zero external dependencies — it uses only Python stdlib + NiFi's `nifiapi` (provided by the runtime).

---

## Step 3: Build the Openflow Pipeline

### Processor 1: ListS3

| Property | Value |
|----------|-------|
| Bucket | `<your-bucket>` |
| Prefix | `x12/` |
| Region | Your S3 region |
| Listing Strategy | `Tracking Timestamps` |

### Processor 2: FetchS3Object

| Property | Value |
|----------|-------|
| Bucket | Same as ListS3 |
| Region | Same as ListS3 |

### Processor 3: SplitContent

| Property | Value |
|----------|-------|
| Byte Sequence | `ST*` |
| Keep Byte Sequence | `Leading` |

Splits a 300MB multi-transaction file into individual transactions at `ST*` boundaries. Each output FlowFile = one transaction set.

### Processor 4: ParseX12ToJSON

| Property | Value |
|----------|-------|
| Output Mode | `ndjson` |
| Include Envelope | `true` |
| Include Raw Segments | `false` |
| Transaction Type Filter | *(leave empty to process all)* |

This is the core processor. It:
- Auto-detects delimiters from the ISA segment
- Parses all segment types using qualifier-aware field maps
- Outputs one JSON object per record (per CLM for 837, per INS for 834, per CLP for 835)
- Sets FlowFile attribute `x12.transaction.types` (e.g., `837`)

### Processor 5: RouteOnAttribute

| Property | Value |
|----------|-------|
| Routing Strategy | `Route to Property name` |
| **route_837** | `${x12.transaction.types:contains('837')}` |
| **route_834** | `${x12.transaction.types:contains('834')}` |
| **route_835** | `${x12.transaction.types:contains('835')}` |

Auto-terminate the `unmatched` relationship.

### Processor 6a: PutSnowpipeStreaming (837 Claims)

| Property | Value |
|----------|-------|
| Account | Your account locator |
| User | Your Snowflake user |
| Role | `ACCOUNTADMIN` |
| Authentication | `Key Pair` |
| Private Key Service | StandardPrivateKeyService |
| Database | `X12_EDI_AI` |
| Schema | `CLAIMS` |
| Table | `LANDING_837_CLAIMS` |
| Record Reader | `JsonTreeReader` |
| Client Lag | `1 sec` |

### Processor 6b: PutSnowpipeStreaming (834 Enrollments)

Same as 6a, except:
| Property | Value |
|----------|-------|
| Schema | `ENROLLMENTS` |
| Table | `LANDING_834_ENROLLMENTS` |

### Processor 6c: PutSnowpipeStreaming (835 Remittances)

Same as 6a, except:
| Property | Value |
|----------|-------|
| Schema | `REMITTANCES` |
| Table | `LANDING_835_REMITTANCES` |

### Controller Services

| Service | Purpose |
|---------|---------|
| **JsonTreeReader** | Parses JSON output from ParseX12ToJSON |
| **StandardPrivateKeyService** | Holds RSA private key for Snowpipe Streaming auth |
| **AWSCredentialsProviderControllerService** | S3 access key + secret |

### Connections Summary

```
ListS3 → FetchS3Object → SplitContent → ParseX12ToJSON → RouteOnAttribute
                                                              │
                                              route_837 → PutSnowpipe (CLAIMS)
                                              route_834 → PutSnowpipe (ENROLLMENTS)
                                              route_835 → PutSnowpipe (REMITTANCES)
```

Auto-terminate: `failure` on all PutSnowpipe processors, `success` on all PutSnowpipe processors, `original` on SplitContent, `unmatched` on RouteOnAttribute.

---

## Step 4: Upload Test Data and Start

```bash
# Upload sample file to S3
aws s3 cp data/sample_837p_20_claims.edi s3://<your-bucket>/x12/

# Start all processors in Openflow
```

---

## Step 5: Verify

```sql
-- Claims landing (immediate)
SELECT COUNT(*) FROM X12_EDI_AI.CLAIMS.LANDING_837_CLAIMS;

-- Gold with AI enrichment (wait ~10 min for Dynamic Table refresh)
SELECT claim_id, subscriber_last_name, primary_diagnosis_code,
       diagnosis_description, diagnosis_category, is_chronic_condition
FROM X12_EDI_AI.GOLD.GOLD_CLAIMS
LIMIT 10;
```

---

## Volume Testing

```bash
# Generate 500K claims (~300MB)
python scripts/generate_x12_claims.py --claims 500000 --output volume_837p_500k.edi

# Upload
aws s3 cp volume_837p_500k.edi s3://<your-bucket>/x12/
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| "IP not allowed to access Snowflake" | Add /24 CIDR for SPCS container IPs to network policy |
| "Snowpipe Streaming does not support DEFAULT" | Landing tables use plain VARCHAR — no defaults |
| PutSnowpipe routing "column not found" | Ensure JsonTreeReader is configured; table column names match parser output exactly (snake_case) |
| ParseX12ToJSON shows 0 records | Check SplitContent output includes ISA header OR set Include Envelope = false |

---

## Repo Structure

```
x12-openflow-quickstart/
├── README.md                                  ← You are here
├── src/x12_processors/
│   ├── ParseX12ToJSON.py                     ← Custom NiFi Python processor
│   ├── field_maps.py                         ← Field mappings for 834/835/837/270/271/276/277
│   ├── __init__.py
│   └── __about__.py
├── sql/
│   ├── 00_prerequisites.sql                  ← Warehouse, network policy, AI access check
│   ├── 01_landing_tables.sql                 ← Typed tables for 837/834/835
│   └── 02_gold_layer.sql                     ← Gold Dynamic Tables + AI enrichment
├── data/
│   └── sample_837p_20_claims.edi             ← 20 test claims (correct X12 format)
├── scripts/
│   └── generate_x12_claims.py                ← Volume test data generator
├── tests/
├── docs/
│   └── blog_x12_openflow_pipeline.html       ← Blog post
└── pyproject.toml
```

---

## How It Works: The Parser

`ParseX12ToJSON` is a pure-Python NiFi FlowFileTransform that:

1. **Detects delimiters** from ISA positions 3/104/105 (handles non-standard files)
2. **Splits segments** using the detected terminator
3. **Routes by qualifier** — `NM1*85` → billing provider, `NM1*IL` → subscriber, `NM1*82` → rendering
4. **Maps fields by position** using `field_maps.py` dictionaries
5. **Handles composite elements** — strips sub-element separator (`:`) from values like `HC:99213`
6. **Sets FlowFile attributes** — `x12.transaction.types`, `x12.record.count`, `mime.type`

Supports: 834, 835, 837, 270, 271, 276, 277.

---

## License

Apache 2.0
