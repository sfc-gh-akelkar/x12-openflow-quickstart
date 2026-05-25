# Screenshots Needed for Quickstart Guide

Place screenshots in this directory. The guide references them as `screenshots/<filename>.png`.

## Required Screenshots

| Filename | Description | Status |
|----------|-------------|--------|
| `nar_upload_success.png` | Extensions tab showing x12-processors NAR with green "Installed" checkmark | Have from session |
| `processor_palette.png` | Add Processor dialog showing ParseX12ToJSON with tags | Have from session |
| `splitrecord_connection.png` | Create Connection dialog: SplitRecord → RouteOnAttribute, "splits" selected | Have from session |
| `routeonattribute_properties.png` | RouteOnAttribute Properties tab showing claims/enrollments/remittances dynamic properties | Have from session |
| `routeonattribute_relationships.png` | RouteOnAttribute Relationships tab with unmatched terminated | Have from session |
| `putsnowpipestreaming_config.png` | PutSnowpipeStreaming Properties showing Account, Database, Schema, Table, Record Reader | Have from session |
| `s3_bucket_files.png` | S3 console showing 3 .edi files under x12/ prefix | Have from session |
| `canvas_complete.png` | Full Openflow canvas showing all processors connected | Needed |
| `data_flowing.png` | Canvas showing FlowFiles moving through (In/Out counters) | Needed |
| `gold_claims_query.png` | Snowsight worksheet showing GOLD_CLAIMS query results | Optional |
| `ai_enriched_results.png` | Snowsight showing clinical_specialty and diagnosis_description columns | Optional |

## Notes

- Screenshots from the conversation session are referenced in the summary context
- Crop to relevant content, avoid showing sensitive info (AWS keys, private keys)
- Recommended dimensions: 1200px wide max for readability
