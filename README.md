# X12 Openflow Processor

Custom NiFi Python processor for parsing HIPAA X12 EDI files into flat JSON records. Packaged as a NAR for import into Snowflake Openflow.

## Supported Transaction Types

| Code | Name | Record Boundary |
|------|------|-----------------|
| 834 | Benefit Enrollment & Maintenance | INS (one record per member) |
| 835 | Health Care Claim Payment/Advice | CLP (one record per claim) |
| 837 | Health Care Claim (Professional/Institutional) | CLM (one record per claim) |
| 270 | Eligibility/Benefit Inquiry | HL (one record per hierarchy level) |
| 271 | Eligibility/Benefit Response | HL (one record per hierarchy level) |
| 276 | Claim Status Request | HL (one record per hierarchy level) |
| 277 | Claim Status Response | HL (one record per hierarchy level) |

## Output Format

Each record is a flat JSON object with human-readable field names:

```json
{
  "transaction_type": "837",
  "transaction_set_control_number": "0003",
  "implementation_guide_version": "005010X222A1",
  "interchange_sender_id": "PROVIDER123",
  "interchange_receiver_id": "PAYER456",
  "claim_id": "CLAIM001",
  "claim_amount": "250.00",
  "billing_provider_npi": "1234567890",
  "subscriber_last_name": "DOE",
  "subscriber_first_name": "JOHN",
  "service_date": "20240115",
  "diagnosis_code_1": "J0600",
  "procedure_code": "99213",
  "service_charge_amount": "250.00",
  "place_of_service": "11"
}
```

## Building the NAR

### Prerequisites

- Python 3.11+
- [Hatch](https://hatch.pypa.io/) build tool

### Build

```bash
pip install hatch hatch-datavolo-nar
hatch build --target nar
```

Output: `dist/x12_processors-0.1.0.nar` (~914 KB)

## Installing in Openflow

### Requirements

- **Medium or Large** Openflow runtime (Python processors not supported on Small)
- Consumes **1 Python processor slot** (max 2 on Medium, 4 on Large)

### Steps

1. Navigate to your Openflow runtime in Snowsight
2. Upload `x12_processors-0.1.0.nar` to the runtime's custom extensions
3. On the Openflow canvas, add the **ParseX12ToJSON** processor
4. Configure processor properties (see below)
5. Connect to your data flow

## Processor Properties

| Property | Required | Default | Description |
|----------|----------|---------|-------------|
| Transaction Type Filter | No | *(empty = all)* | Comma-separated list of transaction types to process (e.g., `834,835,837`) |
| Output Mode | Yes | `ndjson` | `ndjson` (one JSON per line) or `array` (single JSON array) |
| Include Raw Segments | Yes | `false` | Include original segment text in each record |
| Include Envelope | Yes | `true` | Include ISA/GS envelope metadata in each record |

## Output Attributes

The processor sets these FlowFile attributes:

| Attribute | Description |
|-----------|-------------|
| `x12.record.count` | Number of records parsed |
| `x12.transaction.types` | Comma-separated list of transaction types found |
| `mime.type` | Set to `application/json` |

## Example Openflow Flow

```
Source (ListSFTP/FetchSFTP)
    → ParseX12ToJSON
        → PutSnowpipeStreaming (into Snowflake VARIANT column)
```

Or for staging:

```
Source (ListSFTP/FetchSFTP)
    → ParseX12ToJSON
        → PutSnowflakeInternalStageFile
            → (Snowpipe/COPY INTO for loading)
```

## Upgrading

When upgrading the processor:

1. Increment the version in `src/x12_processors/__about__.py`
2. Rebuild: `hatch build --target nar`
3. Upload the new NAR to Openflow
4. If Python processors fail to load after a runtime upgrade, increment the version and re-upload to trigger a venv cache reset

## Running Tests

```bash
python3 tests/test_parser.py
```

## Unmapped Segments

Segments not in the field maps are captured with generic positional keys: `{SEGMENT_ID}_{ELEMENT_INDEX}` (e.g., `BHT_01`, `HL_03`). This ensures no data is silently dropped.

## Project Structure

```
x12-openflow-processor/
├── src/x12_processors/
│   ├── __about__.py          # Version
│   ├── __init__.py
│   ├── field_maps.py         # X12 segment → JSON field mappings
│   └── ParseX12ToJSON.py     # NiFi FlowFileTransform processor
├── tests/
│   ├── test_parser.py        # Unit tests (9 tests)
│   └── sample_data/          # Sample X12 files (834, 835, 837P)
├── pyproject.toml            # Hatch + NAR build config
└── README.md
```
