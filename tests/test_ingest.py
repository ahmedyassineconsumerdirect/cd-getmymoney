from datetime import date
from app.ingest import normalize_owner_name, parse_amount, parse_reported_date


def test_normalize_owner_name():
    assert normalize_owner_name("  John  Smith ") == "JOHN SMITH"
    assert normalize_owner_name("Maria O'Brien") == "MARIA O'BRIEN"
    assert normalize_owner_name("") == ""
    assert normalize_owner_name(None) == ""


def test_parse_amount():
    assert parse_amount("$1,234.56") == 1234.56
    assert parse_amount("1234.56") == 1234.56
    assert parse_amount("") is None
    assert parse_amount(None) is None
    assert parse_amount("garbage") is None


def test_parse_reported_date():
    assert parse_reported_date("2021-06-15") == date(2021, 6, 15)
    assert parse_reported_date("06/15/2021") == date(2021, 6, 15)
    assert parse_reported_date("") is None
    assert parse_reported_date(None) is None
