"""CLI: refresh CA unclaimed property data.

Usage:
    python scripts/refresh_data.py
    python scripts/refresh_data.py --tier 04_From_500_To_Beyond.zip
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingest import TIERS, run

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", action="append", help="Specific tier zip filename (repeatable)")
    args = parser.parse_args()
    tiers = args.tier if args.tier else TIERS
    run(tiers)

if __name__ == "__main__":
    main()
