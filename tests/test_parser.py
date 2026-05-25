import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from x12_processors.field_maps import FIELD_MAPS, ST_CODE_TO_TRANSACTION

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_data")


def _detect_delimiters(raw):
    raw = raw.lstrip()
    isa_pos = raw.find("ISA")
    if isa_pos == -1:
        return None
    isa_start = raw[isa_pos:]
    if len(isa_start) < 106:
        return None
    element_sep = isa_start[3]
    sub_sep = isa_start[104]
    segment_sep = isa_start[105]
    return element_sep, sub_sep, segment_sep


def _split_segments(raw, segment_sep):
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


def _el(elements, idx):
    if idx < len(elements):
        return elements[idx].strip()
    return ""


def _parse_isa(elements):
    return {
        "interchange_sender_id": _el(elements, 6),
        "interchange_receiver_id": _el(elements, 8),
        "interchange_date": _el(elements, 9),
        "interchange_time": _el(elements, 10),
        "interchange_control_number": _el(elements, 13),
        "interchange_usage_indicator": _el(elements, 15),
    }


def _parse_gs(elements):
    return {
        "functional_id_code": _el(elements, 1),
        "application_sender_code": _el(elements, 2),
        "application_receiver_code": _el(elements, 3),
        "group_date": _el(elements, 4),
        "group_time": _el(elements, 5),
        "group_control_number": _el(elements, 6),
        "responsible_agency_code": _el(elements, 7),
        "version_release_industry_code": _el(elements, 8),
    }


def _map_segment(record, tx_type, seg_id, elements, sub_sep):
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
            val = _el(elements, idx)
            if val:
                if sub_sep and sub_sep in val:
                    val = val.split(sub_sep)[0]
                if field_name in record:
                    existing = record[field_name]
                    if isinstance(existing, list):
                        existing.append(val)
                    else:
                        record[field_name] = [existing, val]
                else:
                    record[field_name] = val

    positional_key = f"{seg_id}_{_el(elements, 1) or ''}"
    if positional_key not in field_map and seg_id not in field_map:
        for i, el in enumerate(elements[1:], start=1):
            el_val = el.strip()
            if el_val:
                generic_key = f"{seg_id}_{i:02d}"
                if generic_key not in record:
                    record[generic_key] = el_val


def _finalize_record(records, record, tx_type, allowed_types, include_raw, raw_segs):
    if allowed_types is not None and tx_type not in allowed_types:
        return
    if include_raw:
        record["raw_segments"] = list(raw_segs)
    records.append(record)


def parse_x12(raw, allowed_types=None, include_raw=False, include_envelope=True):
    delimiters = _detect_delimiters(raw)
    assert delimiters is not None, "Cannot detect X12 delimiters"
    element_sep, sub_sep, segment_sep = delimiters

    segments = _split_segments(raw, segment_sep)

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
            envelope = _parse_isa(elements)

        elif seg_id == "GS":
            current_gs = _parse_gs(elements)

        elif seg_id == "ST":
            st_code = elements[1].strip() if len(elements) > 1 else ""
            tx_type = ST_CODE_TO_TRANSACTION.get(st_code, st_code)
            tx_base = {}
            if include_envelope:
                tx_base.update(envelope)
                tx_base.update(current_gs)
            tx_base["transaction_type"] = tx_type
            tx_base["transaction_set_control_number"] = _el(elements, 2)
            if len(elements) > 3:
                tx_base["implementation_guide_version"] = _el(elements, 3)
            boundary_seg = FIELD_MAPS.get(tx_type, {}).get("record_boundary_segment")
            current_record = None
            current_raw = []

        elif seg_id == "SE":
            if current_record is not None:
                _finalize_record(records, current_record, tx_type, allowed_types, include_raw, current_raw)
            elif tx_base is not None and current_record is None:
                _finalize_record(records, dict(tx_base), tx_type, allowed_types, include_raw, current_raw)
            tx_base = None
            current_record = None
            current_raw = []
            tx_type = ""
            boundary_seg = None

        elif tx_base is not None:
            if boundary_seg and seg_id == boundary_seg:
                if current_record is not None:
                    _finalize_record(records, current_record, tx_type, allowed_types, include_raw, current_raw)
                    current_raw = []
                current_record = dict(tx_base)

            if current_record is not None:
                if include_raw:
                    current_raw.append(seg_text)
                _map_segment(current_record, tx_type, seg_id, elements, sub_sep)
            else:
                if include_raw:
                    current_raw.append(seg_text)
                _map_segment(tx_base, tx_type, seg_id, elements, sub_sep)

    return records


def test_delimiter_detection():
    with open(os.path.join(SAMPLE_DIR, "sample_837p.x12")) as f:
        raw = f.read()
    d = _detect_delimiters(raw)
    assert d is not None
    element_sep, sub_sep, segment_sep = d
    assert element_sep == "*"
    assert sub_sep == ":"
    assert segment_sep == "~"


def test_837p_parse():
    with open(os.path.join(SAMPLE_DIR, "sample_837p.x12")) as f:
        raw = f.read()
    records = parse_x12(raw)
    assert len(records) == 2, f"Expected 2 claims, got {len(records)}"

    r1 = records[0]
    assert r1["transaction_type"] == "837"
    assert r1["claim_id"] == "CLAIM001"
    assert r1["claim_amount"] == "250.00"
    assert r1["subscriber_last_name"] == "DOE"
    assert r1["subscriber_first_name"] == "JOHN"
    assert r1["billing_provider_npi"] == "1234567890"
    assert r1["interchange_sender_id"] == "PROVIDER123"
    assert r1["interchange_receiver_id"] == "PAYER456"

    r2 = records[1]
    assert r2["claim_id"] == "CLAIM002"
    assert r2["claim_amount"] == "175.00"


def test_834_parse():
    with open(os.path.join(SAMPLE_DIR, "sample_834.x12")) as f:
        raw = f.read()
    records = parse_x12(raw)
    assert len(records) == 2, f"Expected 2 members (2 INS segments), got {len(records)}"

    r1 = records[0]
    assert r1["transaction_type"] == "834"
    assert r1["member_last_name"] == "DOE"
    assert r1["member_first_name"] == "JOHN"
    assert r1["member_dob"] == "19800515"
    assert r1["member_gender"] == "M"

    r2 = records[1]
    assert r2["member_last_name"] == "SMITH"
    assert r2["member_first_name"] == "JANE"
    assert r2["member_gender"] == "F"


def test_835_parse():
    with open(os.path.join(SAMPLE_DIR, "sample_835.x12")) as f:
        raw = f.read()
    records = parse_x12(raw)
    assert len(records) == 2, f"Expected 2 claims (2 CLP segments), got {len(records)}"

    r1 = records[0]
    assert r1["transaction_type"] == "835"
    assert r1["claim_id"] == "CLM001"
    assert r1["claim_payment_amount"] == "450.00"

    r2 = records[1]
    assert r2["claim_id"] == "CLM002"
    assert r2["claim_payment_amount"] == "225.00"


def test_transaction_filter():
    with open(os.path.join(SAMPLE_DIR, "sample_837p.x12")) as f:
        raw = f.read()
    records = parse_x12(raw, allowed_types={"834"})
    assert len(records) == 0, "837 should be filtered out when only 834 is allowed"

    records = parse_x12(raw, allowed_types={"837"})
    assert len(records) == 2


def test_include_raw_segments():
    with open(os.path.join(SAMPLE_DIR, "sample_837p.x12")) as f:
        raw = f.read()
    records = parse_x12(raw, include_raw=True)
    assert "raw_segments" in records[0]
    assert len(records[0]["raw_segments"]) > 0


def test_exclude_envelope():
    with open(os.path.join(SAMPLE_DIR, "sample_837p.x12")) as f:
        raw = f.read()
    records = parse_x12(raw, include_envelope=False)
    assert "interchange_sender_id" not in records[0]
    assert "functional_id_code" not in records[0]
    assert records[0]["transaction_type"] == "837"


def test_ndjson_output():
    with open(os.path.join(SAMPLE_DIR, "sample_837p.x12")) as f:
        raw = f.read()
    records = parse_x12(raw)
    ndjson = "\n".join(json.dumps(r, default=str) for r in records)
    lines = ndjson.strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert "transaction_type" in parsed


def test_malformed_input():
    try:
        _detect_delimiters("NOT AN X12 FILE")
    except Exception:
        pass
    result = _detect_delimiters("NOT AN X12 FILE")
    assert result is None


if __name__ == "__main__":
    tests = [
        test_delimiter_detection,
        test_837p_parse,
        test_834_parse,
        test_835_parse,
        test_transaction_filter,
        test_include_raw_segments,
        test_exclude_envelope,
        test_ndjson_output,
        test_malformed_input,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{passed+failed} tests passed")
    if failed:
        sys.exit(1)
