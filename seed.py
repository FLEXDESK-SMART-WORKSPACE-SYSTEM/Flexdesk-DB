import argparse
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent / "Flexdesk-backend"
load_dotenv(BACKEND / ".env")

from migrate import PSYCOPG_URL


def seed_catalog(dry_run: bool = False) -> None:
    if dry_run:
        print("Dry run: the location catalog was not changed.")
        return

    sql = (ROOT / "seed" / "locations.sql").read_text(encoding="utf-8")
    with psycopg.connect(PSYCOPG_URL) as connection:
        connection.execute(sql)
        connection.commit()
    print("FLEXDESK location catalog seed completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Idempotently seed the FLEXDESK location catalog.")
    parser.add_argument("--dry-run", action="store_true")
    seed_catalog(parser.parse_args().dry_run)
