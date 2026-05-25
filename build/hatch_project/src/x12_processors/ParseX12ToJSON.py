import json
import io
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, StandardValidators, ExpressionLanguageScope

try:
    from x12_processors.field_maps import FIELD_MAPS, ST_CODE_TO_TRANSACTION
except ImportError:
    from field_maps import FIELD_MAPS, ST_CODE_TO_TRANSACTION


class ParseX12ToJSON(FlowFileTransform):

    class ProcessorDetails:
        version = "0.5.0"
        description = (
            "Parses HIPAA X12 EDI files (834, 835, 837, 270/271, 276/277) "
            "into flat JSON records. Each transaction set produces one JSON "
            "object with human-readable field names."
        )
        tags = ["x12", "edi", "hipaa", "healthcare", "parse", "json", "834", "835", "837"]

    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    TRANSACTION_TYPE_FILTER = PropertyDescriptor(
        name="Transaction Type Filter",
        description=(
            "Comma-separated list of transaction types to process "
            "(e.g. 834,835,837). Leave empty to process all."
        ),
        required=False,
        validators=[StandardValidators.NON_EMPTY_VALIDATOR],
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )

    OUTPUT_MODE = PropertyDescriptor(
        name="Output Mode",
        description=(
            "Controls output format. 'ndjson' writes one JSON object per line. "
            "'array' writes a single JSON array containing all records."
        ),
        required=True,
        default_value="ndjson",
        allowable_values=["ndjson", "array"],
    )

    INCLUDE_RAW_SEGMENTS = PropertyDescriptor(
        name="Include Raw Segments",
        description="When true, each record includes a 'raw_segments' array with the original segment text.",
        required=True,
        default_value="false",
        allowable_values=["true", "false"],
    )

    INCLUDE_ENVELOPE = PropertyDescriptor(
        name="Include Envelope",
        description="When true, ISA/GS envelope metadata is included in each record.",
        required=True,
        default_value="true",
        allowable_values=["true", "false"],
    )

    property_descriptors = [
        TRANSACTION_TYPE_FILTER,
        OUTPUT_MODE,
        INCLUDE_RAW_SEGMENTS,
        INCLUDE_ENVELOPE,
    ]

    def __init__(self, **kwargs):
        super().__init__()

    def getPropertyDescriptors(self):
        return self.property_descriptors

    def transform(self, context, flowfile):
        content_bytes = flowfile.getContentsAsBytes()
        if not content_bytes or len(content_bytes) < 106:
            self.logger.warn(f"Skipping FlowFile: content too short ({len(content_bytes) if content_bytes else 0} bytes), not a valid X12 file")
            return FlowFileTransformResult("failure")
        raw = content_bytes.decode("utf-8", errors="replace")

        tx_filter_val = context.getProperty(self.TRANSACTION_TYPE_FILTER).evaluateAttributeExpressions(flowfile).getValue()
        allowed_types = None
        if tx_filter_val:
            allowed_types = {t.strip() for t in tx_filter_val.split(",")}

        output_mode = context.getProperty(self.OUTPUT_MODE).getValue()
        include_raw = context.getProperty(self.INCLUDE_RAW_SEGMENTS).getValue() == "true"
        include_envelope = context.getProperty(self.INCLUDE_ENVELOPE).getValue() == "true"

        try:
            records = self._parse_x12(raw, allowed_types, include_raw, include_envelope)
        except Exception as e:
            self.logger.error(f"X12 parse error: {e}")
            return FlowFileTransformResult("failure")

        if output_mode == "ndjson":
            output = "\n".join(json.dumps(r, default=str) for r in records)
        else:
            output = json.dumps(records, default=str, indent=2)

        attributes = {
            "x12.record.count": str(len(records)),
            "mime.type": "application/json",
        }
        if records:
            tx_types_found = {r.get("transaction_type", "") for r in records}
            attributes["x12.transaction.types"] = ",".join(sorted(tx_types_found))

        return FlowFileTransformResult("success", contents=output, attributes=attributes)

    def _parse_x12(self, raw, allowed_types, include_raw, include_envelope):
        delimiters = self._detect_delimiters(raw)
        if not delimiters:
            raise ValueError("Cannot detect X12 delimiters: ISA segment not found or too short")

        element_sep, sub_sep, segment_sep = delimiters
        segments = self._split_segments(raw, segment_sep)

        records = []
        envelope = {}
        current_gs = {}
        tx_base = None
        current_record = None
        current_raw = []
        tx_type = ""
        boundary_seg = None

        for seg_text in segments:
            seg_text = seg_text.strip()
            if not seg_text:
                continue

            elements = seg_text.split(element_sep)
            seg_id = elements[0].strip()

            if seg_id == "ISA":
                envelope = self._parse_isa(elements)

            elif seg_id == "GS":
                current_gs = self._parse_gs(elements)

            elif seg_id == "ST":
                st_code = elements[1].strip() if len(elements) > 1 else ""
                tx_type = ST_CODE_TO_TRANSACTION.get(st_code, st_code)
                tx_base = {}
                if include_envelope:
                    tx_base.update(envelope)
                    tx_base.update(current_gs)
                tx_base["transaction_type"] = tx_type
                tx_base["transaction_set_control_number"] = self._el(elements, 2)
                if len(elements) > 3:
                    tx_base["implementation_guide_version"] = self._el(elements, 3)
                boundary_seg = FIELD_MAPS.get(tx_type, {}).get("record_boundary_segment")
                current_record = None
                current_raw = []

            elif seg_id == "SE":
                if current_record is not None:
                    self._finalize_record(records, current_record, tx_type, allowed_types, include_raw, current_raw)
                elif tx_base is not None and current_record is None:
                    self._finalize_record(records, dict(tx_base), tx_type, allowed_types, include_raw, current_raw)
                tx_base = None
                current_record = None
                current_raw = []
                tx_type = ""
                boundary_seg = None

            elif tx_base is not None:
                if boundary_seg and seg_id == boundary_seg:
                    if current_record is not None:
                        self._finalize_record(records, current_record, tx_type, allowed_types, include_raw, current_raw)
                        current_raw = []
                    current_record = dict(tx_base)

                if current_record is not None:
                    if include_raw:
                        current_raw.append(seg_text)
                    self._map_segment(current_record, tx_type, seg_id, elements, sub_sep)
                else:
                    if include_raw:
                        current_raw.append(seg_text)
                    self._map_segment(tx_base, tx_type, seg_id, elements, sub_sep)

        return records

    def _finalize_record(self, records, record, tx_type, allowed_types, include_raw, raw_segs):
        if allowed_types is not None and tx_type not in allowed_types:
            return
        if include_raw:
            record["raw_segments"] = list(raw_segs)
        records.append(record)

    def _detect_delimiters(self, raw):
        raw = raw.lstrip()
        isa_pos = raw.find("ISA")
        if isa_pos == -1:
            return None
        isa_start = raw[isa_pos:]
        if len(isa_start) < 106:
            return None
        element_sep = isa_start[3]
        segment_end_char = isa_start[105]
        sub_sep = isa_start[104]
        return element_sep, sub_sep, segment_end_char

    def _split_segments(self, raw, segment_sep):
        if segment_sep == "~":
            return raw.split("~")
        parts = []
        current = []
        for ch in raw:
            if ch == segment_sep:
                parts.append("".join(current))
                current = []
            else:
                current.append(ch)
        if current:
            parts.append("".join(current))
        return parts

    def _parse_isa(self, elements):
        return {
            "interchange_sender_id": self._el(elements, 6),
            "interchange_receiver_id": self._el(elements, 8),
            "interchange_date": self._el(elements, 9),
            "interchange_time": self._el(elements, 10),
            "interchange_control_number": self._el(elements, 13),
            "interchange_usage_indicator": self._el(elements, 15),
        }

    def _parse_gs(self, elements):
        return {
            "functional_id_code": self._el(elements, 1),
            "application_sender_code": self._el(elements, 2),
            "application_receiver_code": self._el(elements, 3),
            "group_date": self._el(elements, 4),
            "group_time": self._el(elements, 5),
            "group_control_number": self._el(elements, 6),
            "responsible_agency_code": self._el(elements, 7),
            "version_release_industry_code": self._el(elements, 8),
        }

    def _map_segment(self, record, tx_type, seg_id, elements, sub_sep):
        field_map = FIELD_MAPS.get(tx_type, {}).get("fields", {})

        qualifier = ""
        if seg_id in ("NM1", "REF", "AMT", "DTM", "DTP", "N3", "N4") and len(elements) > 1:
            qualifier = elements[1].strip()

        lookup_keys = []
        if qualifier:
            lookup_keys.append(f"{seg_id}_{qualifier}")
        lookup_keys.append(seg_id)

        matched_map = None
        for key in lookup_keys:
            if key in field_map:
                matched_map = field_map[key]
                break

        if matched_map:
            for idx_str, field_name in matched_map.items():
                idx = int(idx_str)
                val = self._el(elements, idx)
                if val:
                    if sub_sep and sub_sep in val:
                        parts = val.split(sub_sep)
                        val = parts[1] if len(parts) > 1 and parts[1] else parts[0]
                    if field_name in record:
                        existing = record[field_name]
                        if isinstance(existing, list):
                            existing.append(val)
                        else:
                            record[field_name] = existing + "; " + val
                    else:
                        record[field_name] = val



    @staticmethod
    def _el(elements, idx):
        if idx < len(elements):
            return elements[idx].strip()
        return ""
