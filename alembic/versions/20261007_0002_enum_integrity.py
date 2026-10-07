"""Enforce PostgreSQL enums and relational integrity constraints.

Revision ID: 20261007_0002
Revises: 20261007_0001
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261007_0002"
down_revision = "20261007_0001"
branch_labels = None
depends_on = None

ENUMS = (
    ("flexdesk_user_role", ("employee", "admin")),
    ("flexdesk_bay_type", ("open", "quiet", "meeting")),
    (
        "flexdesk_workspace_type",
        (
            "desk",
            "hot desk",
            "focus room",
            "meeting room",
            "collaboration space",
            "private workspace",
            "training room",
        ),
    ),
    (
        "flexdesk_workspace_status",
        ("available", "occupied", "maintenance", "unavailable"),
    ),
    ("flexdesk_booking_status", ("confirmed", "cancelled", "completed")),
    (
        "flexdesk_login_event",
        ("login", "logout", "failed_login", "password_reset"),
    ),
)

ENUM_COLUMNS = (
    ("users", "role", "flexdesk_user_role", "employee", False),
    ("bays", "bay_type", "flexdesk_bay_type", None, True),
    ("workspaces", "workspace_type", "flexdesk_workspace_type", None, False),
    (
        "workspaces",
        "status",
        "flexdesk_workspace_status",
        "available",
        False,
    ),
    ("bookings", "status", "flexdesk_booking_status", "confirmed", False),
    ("login_history", "event", "flexdesk_login_event", None, False),
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("FLEXDESK enum migrations require PostgreSQL.")

    inspector = sa.inspect(bind)
    for table in ("users", "locations", "floors", "bays", "workspaces", "bookings", "preferences", "login_history"):
        if table not in inspector.get_table_names():
            raise RuntimeError(f"Expected baseline table {table!r} is missing.")

    for name, values in ENUMS:
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)

    inspector = sa.inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "role" not in user_columns:
        op.add_column(
            "users",
            sa.Column(
                "role",
                postgresql.ENUM(name="flexdesk_user_role", create_type=False),
                nullable=False,
                server_default="employee",
            ),
        )
        bind.execute(
            sa.text("UPDATE users SET role = 'admin' WHERE username = 'admin'")
        )

    for table, column, type_name, default, nullable in ENUM_COLUMNS:
        inspector = sa.inspect(bind)
        column_info = next(
            item for item in inspector.get_columns(table) if item["name"] == column
        )
        if getattr(column_info["type"], "name", None) != type_name:
            allowed_values = dict(ENUMS)[type_name]
            invalid_values = bind.execute(
                sa.text(
                    f'SELECT DISTINCT "{column}" FROM "{table}" '
                    f'WHERE "{column}" IS NOT NULL AND "{column}"::text NOT IN :allowed'
                ).bindparams(sa.bindparam("allowed", expanding=True)),
                {"allowed": allowed_values},
            ).scalars().all()
            if invalid_values:
                raise RuntimeError(
                    f"Cannot migrate {table}.{column}; unsupported values: "
                    f"{', '.join(sorted(map(str, invalid_values)))}"
                )
            default_sql = f"COALESCE({column}::text, '{default}')" if default else f"{column}::text"
            if not nullable and default:
                default_sql = f"COALESCE({column}::text, '{default}')"
            enum_type = postgresql.ENUM(name=type_name, create_type=False)
            if column_info["default"] is not None:
                op.alter_column(
                    table,
                    column,
                    existing_type=column_info["type"],
                    server_default=None,
                )
            op.alter_column(
                table,
                column,
                existing_type=column_info["type"],
                type_=enum_type,
                existing_nullable=column_info["nullable"],
                postgresql_using=f"{default_sql}::{type_name}",
            )
            column_info = next(
                item
                for item in sa.inspect(bind).get_columns(table)
                if item["name"] == column
            )
        if default and not nullable:
            bind.execute(
                sa.text(
                    f'UPDATE "{table}" SET "{column}" = CAST(:default AS {type_name}) '
                    f'WHERE "{column}" IS NULL'
                ),
                {"default": default},
            )
        if column_info["nullable"] != nullable:
            op.alter_column(
                table,
                column,
                existing_type=postgresql.ENUM(name=type_name, create_type=False),
                nullable=nullable,
            )
        if default:
            op.alter_column(
                table,
                column,
                existing_type=postgresql.ENUM(name=type_name, create_type=False),
                server_default=sa.text(f"'{default}'::{type_name}"),
            )

    _ensure_constraints()


def _ensure_constraints() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    unique_constraints = {
        (table, constraint["name"])
        for table in ("locations", "floors", "bays", "workspaces", "bookings", "preferences")
        for constraint in inspector.get_unique_constraints(table)
    }
    unique_specs = (
        ("locations", "uq_locations_name", ["name"]),
        ("floors", "uq_floors_location_name", ["location_id", "name"]),
        ("bays", "uq_bays_floor_name", ["floor_id", "name"]),
        ("workspaces", "uq_workspaces_bay_name", ["bay_id", "name"]),
        (
            "bookings",
            "uq_booking_window",
            ["workspace_id", "booking_date", "start_time", "end_time"],
        ),
    )
    for table, name, columns in unique_specs:
        if (table, name) not in unique_constraints:
            op.create_unique_constraint(name, table, columns)

    foreign_keys = {
        (
            table,
            tuple(item.get("constrained_columns") or ()),
            item.get("referred_table"),
            tuple(item.get("referred_columns") or ()),
        )
        for table in ("floors", "bays", "workspaces", "bookings", "preferences", "login_history")
        for item in inspector.get_foreign_keys(table)
    }
    foreign_key_specs = (
        ("floors", "fk_floors_location", "location_id", "locations", "id", "CASCADE"),
        ("bays", "fk_bays_floor", "floor_id", "floors", "id", "CASCADE"),
        ("workspaces", "fk_workspaces_bay", "bay_id", "bays", "id", "CASCADE"),
        ("bookings", "fk_bookings_user", "user_id", "users", "id", "RESTRICT"),
        ("bookings", "fk_bookings_workspace", "workspace_id", "workspaces", "id", "RESTRICT"),
        ("preferences", "fk_preferences_user", "user_id", "users", "id", "CASCADE"),
        ("login_history", "fk_login_history_user", "user_id", "users", "id", "SET NULL"),
    )
    for table, name, column, referred_table, referred_column, ondelete in foreign_key_specs:
        identity = (table, (column,), referred_table, (referred_column,))
        if identity not in foreign_keys:
            op.create_foreign_key(
                name,
                table,
                referred_table,
                [column],
                [referred_column],
                ondelete=ondelete,
            )

    checks = {
        (table, item.get("name"))
        for table in ("floors", "workspaces", "bookings")
        for item in inspector.get_check_constraints(table)
    }
    check_specs = (
        ("floors", "ck_floors_number_nonnegative", "floor_number >= 0"),
        ("workspaces", "ck_workspaces_capacity_positive", "capacity > 0"),
        (
            "bookings",
            "ck_bookings_valid_time_window",
            "end_time > start_time",
        ),
    )
    for table, name, condition in check_specs:
        if (table, name) not in checks:
            op.create_check_constraint(name, table, condition)

    indexes = {
        (table, item["name"])
        for table in ("users", "floors", "bays", "workspaces", "bookings", "login_history")
        for item in inspector.get_indexes(table)
    }
    index_specs = (
        ("users", "ix_users_username", ["username"]),
        ("users", "ix_users_entra_subject", ["entra_subject"]),
        ("floors", "ix_floors_location_id", ["location_id"]),
        ("bays", "ix_bays_floor_id", ["floor_id"]),
        ("workspaces", "ix_workspaces_bay_id", ["bay_id"]),
        ("workspaces", "ix_workspaces_workspace_type", ["workspace_type"]),
        ("bookings", "ix_bookings_user_id", ["user_id"]),
        ("bookings", "ix_bookings_workspace_id", ["workspace_id"]),
        ("bookings", "ix_bookings_booking_date", ["booking_date"]),
        ("bookings", "ix_bookings_status", ["status"]),
        ("login_history", "ix_login_history_user_id", ["user_id"]),
    )
    for table, name, columns in index_specs:
        if (table, name) not in indexes:
            op.create_index(name, table, columns)


def downgrade() -> None:
    raise RuntimeError(
        "Enum constraints protect existing workspace and booking data; "
        "restore from a verified database backup instead of downgrading."
    )
