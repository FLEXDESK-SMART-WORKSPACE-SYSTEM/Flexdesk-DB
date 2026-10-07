# Flexdesk-DB

PostgreSQL schema, versioned migrations, repeatable location seed data, and SQL integrity checks for FLEXDESK.

## Schema

`models.py` is the SQLAlchemy representation of the relational schema. `alembic/versions` is the versioned migration history; the migrations create PostgreSQL enum types and enforce the table, foreign-key, uniqueness, and check constraints. The existing SQL files under `migrations/` are retained as the legacy bootstrap and are applied once by `migrate.py`.

The core relations are:

- `users` — employee account, hashed password, optional department, and access role.
- `locations` → `floors` → `bays` → `workspaces` — office hierarchy and inventory.
- `bookings` — employee, workspace, date, time window, and booking status.
- `preferences` — one preference row per employee.
- `login_history` — login, logout, failed-login, and password-reset audit events.

PostgreSQL enum types restrict account roles, bay/workspace types, workspace and booking statuses, and login events. Foreign keys, unique keys, positive-capacity/floor checks, and valid booking time windows protect relational integrity. Existing account identifiers and authentication behavior are preserved; no additional login identifier is introduced.

## Migration

Use the backend Python environment and database URL from `Flexdesk-backend/.env`. Run the legacy bootstrap first, then the backend's existing authentication revisions, then this repository's Alembic revisions:

```powershell
Set-Location ..\Flexdesk-backend
.\.venv311\Scripts\python.exe ..\Flexdesk-DB\migrate.py
.\.venv311\Scripts\python.exe -m alembic -c .\alembic.ini upgrade head
.\.venv311\Scripts\python.exe -m alembic -c ..\Flexdesk-DB\alembic.ini upgrade head
```

The database migration is repeatable: `migrate.py` records each legacy SQL file, and Alembic records the schema revision in `alembic_version`. Enum conversion fails rather than silently discarding values that do not belong to the declared type.

## Seed

After migrations, seed the canonical locations. The inserts are idempotent and do not overwrite a location address:

```powershell
Set-Location ..\Flexdesk-backend
.\.venv311\Scripts\python.exe ..\Flexdesk-DB\seed.py
```

Preview the seed command without connecting to or modifying the database:

```powershell
.\.venv311\Scripts\python.exe ..\Flexdesk-DB\seed.py --dry-run
```

## SQL checks

Run `sql/integrity_audit.sql` with `psql` after a migration or seed. Orphan, invalid-capacity, and invalid-time-window rows should be absent. The remaining result sets display the installed enum values and current Alembic revision.
