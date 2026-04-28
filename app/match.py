"""Match service interface + demo exact-match implementation.

Production swaps DemoExactMatcher for Consumer Direct's existing
data-broker matching service by implementing the MatchService protocol.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Protocol

import duckdb

from app.ingest import normalize_owner_name


@dataclass
class Match:
    record_id: int
    holder_name: str
    owner_name: str
    last_known_address: str | None
    last_known_city: str | None
    last_known_state: str | None
    last_known_zip: str | None
    amount_min: float | None
    amount_max: float | None
    property_type: str | None
    reported_date: date | None


class MatchService(Protocol):
    def find_matches(
        self,
        first_name: str,
        last_name: str,
        dob: date | None = None,
        addresses: list[str] | None = None,
    ) -> list[Match]: ...


class DemoExactMatcher:
    """Exact match on UPPER(TRIM(first + ' ' + last)).

    Sufficient for the prototype; production uses CD's existing matcher.
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def find_matches(
        self,
        first_name: str,
        last_name: str,
        dob: date | None = None,
        addresses: list[str] | None = None,
    ) -> list[Match]:
        normalized = normalize_owner_name(f"{first_name} {last_name}")
        if not normalized:
            return []
        rows = self.conn.execute(
            """
            SELECT record_id, holder_name, owner_name,
                   last_known_address, last_known_city,
                   last_known_state, last_known_zip,
                   amount_min, amount_max,
                   property_type, reported_date
            FROM ca_unclaimed
            WHERE owner_name_normalized = ?
            ORDER BY COALESCE(amount_max, 0) DESC
            LIMIT 100
            """,
            [normalized],
        ).fetchall()
        return [Match(*r) for r in rows]
