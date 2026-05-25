# x12-openflow-quickstart

**Production-grade X12 EDI ingestion with Snowflake Openflow + Cortex AI.**

Ingest HIPAA X12 healthcare transactions (837 Claims, 834 Enrollments, 835 Remittances) from S3 into Snowflake — parsed in-flight by a custom Python processor, routed by transaction type, and enriched with Cortex AI.

```
S3 (.edi files)
  → ListS3 → FetchS3
    → ParseX12ToJSON (custom Python processor)
      → SplitRecord (one record per JSON line)
        → RouteOnAttribute (by x12.transaction.types)
          → PutSnowpipeStreaming → CLAIMS.LANDING_837_CLAIMS
          → PutSnowpipeStreaming → ENROLLMENTS.LANDING_834_ENROLLMENTS
          → PutSnowpipeStreaming → REMITTANCES.LANDING_835_REMITTANCES
            → Dynamic Tables (GOLD layer + Cortex AI)
```

---

## Quick Start

```bash
# 1. Run SQL setup
#    Execute sql/00_prerequisites.sql, sql/01_landing_tables.sql, sql/02_gold_layer.sql

# 2. Build the NAR
pip install hatch hatch-datavolo-nar
cd build/hatch_project && hatch build --target nar

# 3. Upload NAR to Openflow (Extensions → Upload NAR)

# 4. Upload sample data to S3
aws s3 cp data/sample_837p_20_claims.edi s3://your-bucket/x12/
aws s3 cp data/sample_834_10_enrollments.edi s3://your-bucket/x12/
aws s3 cp data/sample_835_10_remittances.edi s3://your-bucket/x12/

# 5. Configure and start the Openflow canvas
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  S3 BUCKET (x12/ prefix)                                     │
│  .edi files: 834, 835, 837                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  OPENFLOW (NiFi on SPCS)                                     │
│                                                               │
│  ListS3 → FetchS3 → ParseX12ToJSON → SplitRecord            │
│                                          │                    │
│                                  RouteOnAttribute             │
│                              ┌───────┼───────┐               │
│                              ↓       ↓       ↓               │
│                            837     834     835               │
│                              ↓       ↓       ↓               │
│                      PutSnowpipeStreaming (×3)                │
└──────────────────────────┬──────────────────────────────────┘
                           │ Snowpipe Streaming
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  LANDING TABLES                                              │
│  • CLAIMS.LANDING_837_CLAIMS (79 columns)                    │
│  • ENROLLMENTS.LANDING_834_ENROLLMENTS (57 columns)          │
│  • REMITTANCES.LANDING_835_REMITTANCES (53 columns)          │
└──────────────────────────┬──────────────────────────────────┘
                           │ Dynamic Tables (1 min lag)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  GOLD LAYER                                                  │
│  • GOLD_CLAIMS (claims + remittances joined, payment status) │
│  • GOLD_ENROLLMENTS (typed dates, status descriptions)       │
│  • GOLD_REMITTANCES (payment analytics)                      │
│  • GOLD_CLAIMS_AI_ENRICHED (Cortex AI clinical specialty)    │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Snowflake account with ACCOUNTADMIN access
- Openflow enabled (Snowpark Container Services)
- S3 bucket with IAM credentials
- RSA key pair (PKCS8, unencrypted) for Snowpipe Streaming
- Network policy allowing SPCS container IPs
- Python 3.9+ with `hatch` and `hatch-datavolo-nar`

---

## Building the NAR

> **Quick start:** To get started immediately, upload `x12_processors-0.5.0.nar` from the repo root directly to Openflow (Extensions → Upload NAR). To customize field mappings or build from source, follow the steps below.

```bash
pip install hatch hatch-datavolo-nar
cd build/hatch_project
hatch build --target nar
# Output: dist/x12_processors-0.5.0.nar
```

Upload via Openflow UI → Extensions → Upload NAR.

---

## Openflow Canvas Configuration

| Processor | Key Properties |
|-----------|---------------|
| **ListS3** | Bucket, Prefix=`x12/`, Region |
| **FetchS3** | Same bucket/region |
| **ParseX12ToJSON** | Output Mode=`ndjson`, Include Envelope=`true` |
| **SplitRecord** | Reader=JsonTreeReader, Writer=JsonRecordSetWriter |
| **RouteOnAttribute** | claims=`${x12.transaction.types:contains('837')}`, enrollments=`...834...`, remittances=`...835...` |
| **PutSnowpipeStreaming** (×3) | Account, User, Role=ACCOUNTADMIN, Database=X12_EDI_AI, Schema/Table per type |

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| "NAR content is missing META-INF/MANIFEST" | Use `hatch build --target nar`, not manual zip |
| Processor shows "Invalid" | Use try/except import pattern for field_maps |
| "ISA segment not found" | 0-byte S3 directory markers — upload files flat |
| "Authorization failed" | Add SPCS IPs to network policy (check LOGIN_HISTORY) |
| `SchemaMismatchException` | Table must have ALL columns matching JSON field names |
| `[Ljava.lang.Object;@...` | Parser must output strings, not arrays — use v0.5.0+ |

---

## Repo Structure

```
x12-openflow-quickstart/
├── README.md
├── src/x12_processors/
│   ├── ParseX12ToJSON.py          # Custom NiFi Python processor
│   ├── field_maps.py              # X12 segment → field mappings (834/835/837/270-277)
│   └── __init__.py
├── build/hatch_project/
│   └── pyproject.toml             # NAR build configuration
├── sql/
│   ├── 00_prerequisites.sql       # Warehouse, database, key pair, network policy
│   ├── 01_landing_tables.sql      # Landing tables (all columns, schema evolution)
│   └── 02_gold_layer.sql          # Dynamic Tables + Cortex AI enrichment
├── data/
│   ├── sample_834_10_enrollments.edi
│   ├── sample_835_10_remittances.edi
│   └── sample_837p_20_claims.edi
├── blog/
│   └── x12_openflow_quickstart.md # Full blog post / quickstart guide
└── .gitignore
```

---

## License

Apache 2.0
