from datetime import datetime
from app.db import get_connection, ensure_schema
from app.match import DemoExactMatcher

def _seed(conn):
    # CA State Controller stores owner names "LAST FIRST" (see app/match.py
    # index narrowing and scripts/customer_match_fast.py), so fixtures match.
    conn.execute("""
        INSERT INTO ca_unclaimed VALUES
        (1, 'WELLS FARGO', 'WF1', 'SMITH JOHN', 'SMITH JOHN',
         '123 Main St', 'San Francisco', 'CA', '94102',
         2150.00, 2150.00, 'Savings Account', '2021-06-15',
         'test', CURRENT_TIMESTAMP),
        (2, 'CHARLES SCHWAB', 'SCHWAB', 'SMITH JOHN', 'SMITH JOHN',
         '456 Oak Ave', 'San Jose', 'CA', '95110',
         1580.50, 1580.50, 'Brokerage', '2020-03-10',
         'test', CURRENT_TIMESTAMP),
        (3, 'BANK OF AMERICA', 'BOA1', 'DOE JANE', 'DOE JANE',
         '789 Pine St', 'Los Angeles', 'CA', '90001',
         50.00, 50.00, 'Checking', '2022-01-20',
         'test', CURRENT_TIMESTAMP)
    """)

def test_exact_match_finds_records(tmp_path):
    conn = get_connection(str(tmp_path / "t.duckdb"))
    ensure_schema(conn)
    _seed(conn)
    matcher = DemoExactMatcher(conn)
    matches = matcher.find_matches(first_name="John", last_name="Smith")
    assert len(matches) == 2
    assert all(m.owner_name == "SMITH JOHN" for m in matches)
    assert matches[0].amount_max >= matches[1].amount_max  # ordered desc
    conn.close()

def test_exact_match_no_results(tmp_path):
    conn = get_connection(str(tmp_path / "t.duckdb"))
    ensure_schema(conn)
    _seed(conn)
    matcher = DemoExactMatcher(conn)
    matches = matcher.find_matches(first_name="Nobody", last_name="Findme")
    assert matches == []
    conn.close()

def test_exact_match_normalizes_input(tmp_path):
    conn = get_connection(str(tmp_path / "t.duckdb"))
    ensure_schema(conn)
    _seed(conn)
    matcher = DemoExactMatcher(conn)
    matches = matcher.find_matches(first_name="  john  ", last_name="smith")
    assert len(matches) == 2
    conn.close()
