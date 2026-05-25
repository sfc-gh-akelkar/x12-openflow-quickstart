# Building a Real-Time X12 EDI Pipeline with Snowflake Openflow and Cortex AI

Healthcare organizations process millions of X12 EDI transactions daily — enrollment files (834), claims (837), and remittance advice (835). These fixed-width, segment-delimited files are notoriously difficult to parse and integrate into modern analytics platforms.

In this quickstart, we build a **production-grade streaming pipeline** that:

1. Ingests raw X12 EDI files from S3
2. Parses them into structured JSON using a custom Openflow (NiFi) processor
3. Routes records by transaction type into typed Snowflake tables
4. Materializes analytics-ready Gold layer views with Dynamic Tables
5. Enriches claims with AI-generated clinical classifications via Cortex AI

**Architecture:**

```
S3 (.edi files)
    → ListS3 → FetchS3
        → ParseX12ToJSON (custom Python processor)
            → SplitRecord (one record per JSON line)
                → RouteOnAttribute (by transaction_type)
                    → PutSnowpipeStreaming → LANDING_837_CLAIMS
                    → PutSnowpipeStreaming → LANDING_834_ENROLLMENTS
                    → PutSnowpipeStreaming → LANDING_835_REMITTANCES
                        → Dynamic Tables (GOLD layer)
                            → Cortex AI (clinical specialty classification)
```

---

## Prerequisites

- Snowflake account with Openflow enabled
- S3 bucket with IAM credentials
- RSA key pair for Snowpipe Streaming authentication
- Python 3.9+ with `hatch` and `hatch-datavolo-nar` installed

---

## Step 1: Build the Custom ParseX12ToJSON Processor

X12 EDI files are self-describing — the ISA segment declares delimiters:
- Position 3: element separator (typically `*`)
- Position 104: sub-element separator (typically `:`)
- Position 105: segment terminator (typically `~`)

Our processor reads these delimiters, splits the file into segments, and maps each segment's elements to human-readable field names using a configurable field map.

### Key Design Decisions

1. **Record boundaries** — Each transaction type has a boundary segment that starts a new record:
   - 834: `INS` (one record per member enrollment action)
   - 835: `CLP` (one record per claim payment)
   - 837: `CLM` (one record per submitted claim)

2. **Composite sub-elements** — Fields like diagnosis codes use composite format (`ABK:J0690`). The parser extracts the code portion (after the separator), not the qualifier.

3. **Multi-value handling** — When a claim has multiple service lines, values are semicolon-separated (e.g., `"99213; 85025"`). This keeps the output flat for Snowpipe Streaming.

4. **NDJSON output** — One JSON object per line, enabling SplitRecord to fan out individual records for routing.

### Building the NAR

Openflow requires Python processors packaged as NAR (NiFi Archive) files:

```bash
pip install hatch hatch-datavolo-nar

# pyproject.toml
[build-system]
requires = ["hatchling", "hatch-datavolo-nar"]
build-backend = "hatchling.build"

[project]
name = "x12-processors"
version = "0.5.0"

[tool.hatch.build.targets.nar]
packages = ["src/x12_processors"]
```

```bash
hatch build --target nar
# Output: dist/x12_processors-0.5.0.nar
```

Upload the NAR via Openflow UI → Extensions → Upload NAR.

> **Tip:** If your processor shows "Invalid" after upload, check the Python import paths. NiFi loads `.py` files flat — use a try/except import pattern:
> ```python
> try:
>     from x12_processors.field_maps import FIELD_MAPS
> except ImportError:
>     from field_maps import FIELD_MAPS
> ```

---

## Step 2: Configure the Openflow Canvas

### ListS3 → FetchS3
- **Bucket:** `your-bucket-name`
- **Prefix:** `x12/`
- **Region:** `us-west-2`

> **Gotcha:** ListS3 picks up S3 directory marker objects (0-byte files). Upload `.edi` files flat under your prefix — no subfolders.

### ParseX12ToJSON
- **Output Mode:** `ndjson`
- **Include Envelope:** `true`
- **Include Raw Segments:** `false`

### SplitRecord
- **Record Reader:** JsonTreeReader
- **Record Writer:** JsonRecordSetWriter
- Connect: `splits` → RouteOnAttribute
- Auto-terminate: `original`, `failure`

### RouteOnAttribute
Add three dynamic properties:
| Property Name | Value |
|---|---|
| `claims` | `${x12.transaction.types:contains('837')}` |
| `enrollments` | `${x12.transaction.types:contains('834')}` |
| `remittances` | `${x12.transaction.types:contains('835')}` |

Auto-terminate: `unmatched`

### PutSnowpipeStreaming (×3)
Each instance targets a different table:
- **Account:** `organization-account` (e.g., `sfsenorthamerica-demo_akelkar`)
- **Database:** `X12_EDI_AI`
- **Schema:** `CLAIMS` / `ENROLLMENTS` / `REMITTANCES`
- **Table:** `LANDING_837_CLAIMS` / `LANDING_834_ENROLLMENTS` / `LANDING_835_REMITTANCES`
- **Record Reader:** JsonTreeReader
- **Private Key Service:** StandardPrivateKeyService (RSA key, no passphrase)
- **Role:** `ACCOUNTADMIN`

---

## Step 3: Create Snowflake Landing Tables

The tables must have columns matching **every field** the parser outputs. PutSnowpipeStreaming does strict client-side column validation — any JSON field without a matching column causes a `SchemaMismatchException`.

We enable `SCHEMA_EVOLUTION` as a safety net for future field additions:

```sql
CREATE TABLE X12_EDI_AI.CLAIMS.LANDING_837_CLAIMS (
    claim_id VARCHAR,
    claim_amount VARCHAR,
    diagnosis_code_1 VARCHAR,
    -- ... (79 columns total for 837)
) ENABLE_SCHEMA_EVOLUTION = TRUE;
```

See `sql/01_landing_tables.sql` for the complete DDL.

---

## Step 4: Gold Layer Dynamic Tables

Dynamic Tables automatically refresh as new data lands:

```sql
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
LEFT JOIN X12_EDI_AI.REMITTANCES.LANDING_835_REMITTANCES r
    ON c.claim_id = r.claim_id;
```

---

## Step 5: Cortex AI Enrichment

The real power comes from combining structured EDI data with Snowflake's built-in LLMs. We create a view that classifies each claim by clinical specialty:

```sql
CREATE VIEW X12_EDI_AI.GOLD.GOLD_CLAIMS_AI_ENRICHED AS
SELECT
    gc.*,
    SNOWFLAKE.CORTEX.COMPLETE('claude-sonnet-4-6',
        'Given ICD-10 code "' || gc.diagnosis_code_1
        || '", respond with ONLY the medical specialty name. One or two words max.'
    ) as clinical_specialty
FROM X12_EDI_AI.GOLD.GOLD_CLAIMS gc;
```

**Result:**

| claim_id | diagnosis_code_1 | clinical_specialty | claim_amount | payment_status |
|---|---|---|---|---|
| CLM00000004 | J06.9 | Otolaryngology | 385.02 | PAID |
| CLM00000003 | R10.9 | Gastroenterology | 945.25 | PAID |
| CLM00000009 | E11.9 | Endocrinology | 140.47 | PAID |
| CLM00000006 | M79.3 | Rheumatology | 741.23 | PAID |

---

## Troubleshooting Guide

| Error | Cause | Fix |
|---|---|---|
| "NAR content is missing required META-INF/MANIFEST entry" | Manual zip instead of hatch build | Use `hatch build --target nar` |
| Processor shows "Invalid" with empty Properties | Python import path fails in NiFi | Use try/except import pattern |
| "ISA segment not found or too short" | 0-byte S3 directory markers | Upload files flat, no subfolders |
| "Authorization failed after retry" | Network policy blocking SPCS IPs | Add Openflow runtime IPs to network policy |
| `SchemaMismatchException: [field_name]` | Table missing a column | Add the column, or remove generic fallback from parser |
| `[Ljava.lang.Object;@...` in table | JSON arrays not supported by Record Reader | Concatenate multi-values as semicolon strings |

---

## Production Considerations

- **Scaling:** Openflow auto-scales with concurrent tasks. PutSnowpipeStreaming supports multiple channels per table.
- **Exactly-once delivery:** PutSnowpipeStreaming v1 supports exactly-once via channel offset tracking.
- **Schema drift:** `ENABLE_SCHEMA_EVOLUTION` handles new fields from updated EDI guides.
- **Monitoring:** Use Openflow bulletins + Snowflake's `COPY_HISTORY` / login history for end-to-end observability.
- **Cost:** Dynamic Tables with `TARGET_LAG = '1 minute'` use warehouse credits only during refresh.

---

## Repository Structure

```
x12-openflow-quickstart/
├── src/x12_processors/
│   ├── ParseX12ToJSON.py     # Custom NiFi Python processor
│   ├── field_maps.py         # X12 segment → field name mappings
│   └── __init__.py
├── build/hatch_project/
│   └── pyproject.toml        # NAR build configuration
├── sql/
│   ├── 00_prerequisites.sql  # Warehouse, database, key pair
│   ├── 01_landing_tables.sql # Landing tables with all columns
│   └── 02_gold_layer.sql     # Dynamic Tables + AI view
├── data/
│   ├── sample_834_10_enrollments.edi
│   ├── sample_835_10_remittances.edi
│   └── sample_837p_20_claims.edi
└── README.md
```

---

## Next Steps

- Add 270/271 (eligibility) and 276/277 (claim status) transaction types
- Build a Streamlit dashboard for claims analytics
- Create a Cortex Agent for natural-language queries over EDI data
- Set up alerting on denied claims or enrollment anomalies

---

*Built with Snowflake Openflow, Snowpipe Streaming, Dynamic Tables, and Cortex AI.*
