"""
MigrateIQ ABAP Scanner Test Suite
Verifies all 10 simplification rules, positive/negative test cases, and precision/recall.
"""

import pytest
from app.scanner.engine import ABAPScanner
from app.scanner.rules import RULES

scanner = ABAPScanner()

def test_rule_r001_bseg_detection():
    # Positive case: direct read of BSEG
    code_pos = "SELECT * FROM bseg INTO TABLE lt_bseg WHERE bukrs = '1000'."
    res = scanner.scan_code(code_pos, "test_r001.abap")
    assert any(f["rule_id"] == "R001" for f in res["findings"])

    # Negative case: comment or ACDOCA
    code_neg = "* SELECT * FROM bseg is commented\nSELECT * FROM acdoca INTO TABLE lt_acdoca."
    res = scanner.scan_code(code_neg, "test_r001_neg.abap")
    assert not any(f["rule_id"] == "R001" for f in res["findings"])

def test_rule_r002_vbuk_detection():
    # Positive case
    code_pos = "SELECT * FROM vbuk INTO TABLE lt_vbuk WHERE vbeln = '123'."
    res = scanner.scan_code(code_pos)
    assert any(f["rule_id"] == "R002" for f in res["findings"])

    # Negative case: modern read from VBAK
    code_neg = "SELECT vbeln, gbstk FROM vbak INTO TABLE lt_orders."
    res = scanner.scan_code(code_neg)
    assert not any(f["rule_id"] == "R002" for f in res["findings"])

def test_rule_r003_mseg_detection():
    # Positive case
    code_pos = "SELECT * FROM mseg INTO TABLE lt_mseg."
    res = scanner.scan_code(code_pos)
    assert any(f["rule_id"] == "R003" for f in res["findings"])

    # Negative case: MATDOC
    code_neg = "SELECT * FROM matdoc INTO TABLE lt_matdoc."
    res = scanner.scan_code(code_neg)
    assert not any(f["rule_id"] == "R003" for f in res["findings"])

def test_rule_r005_matnr_length():
    # Positive case: hardcoded 18 chars
    code_pos = "DATA: lv_matnr TYPE c LENGTH 18."
    res = scanner.scan_code(code_pos)
    assert any(f["rule_id"] == "R005" for f in res["findings"])

    # Negative case: standard TYPE matnr
    code_neg = "DATA: lv_matnr TYPE matnr."
    res = scanner.scan_code(code_neg)
    assert not any(f["rule_id"] == "R005" for f in res["findings"])

def test_rule_r006_konv():
    # Positive case: KONV pricing cluster
    code_pos = "SELECT * FROM konv INTO TABLE lt_konv WHERE knumv = '100'."
    res = scanner.scan_code(code_pos)
    assert any(f["rule_id"] == "R006" for f in res["findings"])

    # Negative case: PRCD_ELEMENTS
    code_neg = "SELECT * FROM prcd_elements INTO TABLE lt_prcd."
    res = scanner.scan_code(code_neg)
    assert not any(f["rule_id"] == "R006" for f in res["findings"])

def test_rule_r008_native_sql():
    # Positive case: EXEC SQL
    code_pos = "EXEC SQL.\nSELECT * FROM BKPF\nENDEXEC."
    res = scanner.scan_code(code_pos)
    assert any(f["rule_id"] == "R008" for f in res["findings"])

    # Negative case: Open SQL
    code_neg = "SELECT belnr, bukrs FROM bkpf INTO TABLE lt_bkpf."
    res = scanner.scan_code(code_neg)
    assert not any(f["rule_id"] == "R008" for f in res["findings"])

def test_clean_file_zero_findings():
    with open("tests/samples/z_clean_code.abap", "r") as f:
        clean_code = f.read()
    res = scanner.scan_code(clean_code, "z_clean_code.abap")
    assert res["total_findings"] == 0

def test_bad_file_triggers_multiple_rules():
    with open("tests/samples/z_fi_report_bad.abap", "r") as f:
        bad_fi = f.read()
    res = scanner.scan_code(bad_fi, "z_fi_report_bad.abap")
    rule_ids = {f["rule_id"] for f in res["findings"]}
    assert "R001" in rule_ids
    assert "R008" in rule_ids
    assert "R009" in rule_ids
    assert "R010" in rule_ids

def test_scanner_precision_and_recall():
    """
    Evaluates precision and recall across labeled test snippets as required in Section 10.2.
    """
    labeled_dataset = [
        {"code": "SELECT * FROM bseg INTO TABLE lt.", "expected_rules": ["R001"]},
        {"code": "SELECT * FROM vbuk WHERE vbeln = '1'.", "expected_rules": ["R002"]},
        {"code": "SELECT * FROM mseg INTO TABLE lt.", "expected_rules": ["R003"]},
        {"code": "UPDATE kna1 SET sortl = 'A'.", "expected_rules": ["R004"]},
        {"code": "DATA: matnr(18) TYPE c.", "expected_rules": ["R005"]},
        {"code": "SELECT * FROM konv INTO TABLE lt.", "expected_rules": ["R006"]},
        {"code": "CALL FUNCTION 'WS_DELIVERY_UPDATE'.", "expected_rules": ["R007"]},
        {"code": "EXEC SQL.", "expected_rules": ["R008"]},
        {"code": "UPDATE mara SET mtart = 'F'.", "expected_rules": ["R009"]},
        {"code": "SELECT * FROM vbak CLIENT SPECIFIED.", "expected_rules": ["R010"]},
        # Negative / clean samples
        {"code": "SELECT * FROM acdoca INTO TABLE lt.", "expected_rules": []},
        {"code": "DATA: lv_matnr TYPE matnr.", "expected_rules": []},
        {"code": "* SELECT * FROM bseg is a comment", "expected_rules": []}
    ]

    total_true_positives = 0
    total_false_positives = 0
    total_false_negatives = 0

    for item in labeled_dataset:
        scan_res = scanner.scan_code(item["code"])
        detected = {f["rule_id"] for f in scan_res["findings"]}
        expected = set(item["expected_rules"])

        tp = len(detected.intersection(expected))
        fp = len(detected - expected)
        fn = len(expected - detected)

        total_true_positives += tp
        total_false_positives += fp
        total_false_negatives += fn

    precision = total_true_positives / (total_true_positives + total_false_positives) if (total_true_positives + total_false_positives) > 0 else 1.0
    recall = total_true_positives / (total_true_positives + total_false_negatives) if (total_true_positives + total_false_negatives) > 0 else 1.0

    assert precision >= 0.90, f"Scanner precision was {precision:.2f}, expected >= 0.90"
    assert recall >= 0.90, f"Scanner recall was {recall:.2f}, expected >= 0.90"
