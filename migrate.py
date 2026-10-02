from pathlib import Path
import os

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent / "Flexdesk-backend"
load_dotenv(BACKEND / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:5432@127.0.0.1:5432/flexdesk")
PSYCOPG_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)


def ensure_database() -> None:
    admin_url = PSYCOPG_URL.rsplit("/", 1)[0] + "/postgres"
    with psycopg.connect(admin_url, autocommit=True) as connection:
        exists = connection.execute("SELECT 1 FROM pg_database WHERE datname = 'flexdesk'").fetchone()
        if not exists:
            connection.execute('CREATE DATABASE flexdesk')


def migrate() -> None:
    ensure_database()
    with psycopg.connect(PSYCOPG_URL) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version VARCHAR(100) PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        for path in sorted((ROOT / "migrations").glob("*.sql")):
            version = path.name
            if connection.execute("SELECT 1 FROM schema_migrations WHERE version = %s", (version,)).fetchone():
                continue
            connection.execute(path.read_text(encoding="utf-8"))
            connection.execute("INSERT INTO schema_migrations(version) VALUES (%s) ON CONFLICT DO NOTHING", (version,))
        connection.commit()
    print("Flexdb migrations completed")


if __name__ == "__main__":
    migrate()
