from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    ADMIN = "admin"


class BayType(str, Enum):
    OPEN = "open"
    QUIET = "quiet"
    MEETING = "meeting"


class WorkspaceType(str, Enum):
    DESK = "desk"
    HOT_DESK = "hot desk"
    FOCUS_ROOM = "focus room"
    MEETING_ROOM = "meeting room"
    COLLABORATION_SPACE = "collaboration space"
    PRIVATE_WORKSPACE = "private workspace"
    TRAINING_ROOM = "training room"


class WorkspaceStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"


class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class LoginEvent(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    PASSWORD_RESET = "password_reset"


def enum_column(enum_class: type[Enum], name: str) -> SqlEnum:
    return SqlEnum(
        enum_class,
        name=name,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_username", "username", unique=True),
        Index("ix_users_entra_subject", "entra_subject", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    department: Mapped[str | None] = mapped_column(String(120))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    entra_subject: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        enum_column(UserRole, "flexdesk_user_role"),
        nullable=False,
        default=UserRole.EMPLOYEE,
        server_default=UserRole.EMPLOYEE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("name", name="uq_locations_name"),
        Index("ix_locations_city", "city"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))


class Floor(Base):
    __tablename__ = "floors"
    __table_args__ = (
        UniqueConstraint("location_id", "name", name="uq_floors_location_name"),
        CheckConstraint("floor_number >= 0", name="ck_floors_number_nonnegative"),
        Index("ix_floors_location_id", "location_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)


class Bay(Base):
    __tablename__ = "bays"
    __table_args__ = (
        UniqueConstraint("floor_id", "name", name="uq_bays_floor_name"),
        Index("ix_bays_floor_id", "floor_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    floor_id: Mapped[int] = mapped_column(
        ForeignKey("floors.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    bay_type: Mapped[BayType | None] = mapped_column(
        enum_column(BayType, "flexdesk_bay_type")
    )


class Workspace(Base):
    __tablename__ = "workspaces"
    __table_args__ = (
        UniqueConstraint("bay_id", "name", name="uq_workspaces_bay_name"),
        CheckConstraint("capacity > 0", name="ck_workspaces_capacity_positive"),
        Index("ix_workspaces_bay_id", "bay_id"),
        Index("ix_workspaces_workspace_type", "workspace_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bay_id: Mapped[int] = mapped_column(
        ForeignKey("bays.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    workspace_type: Mapped[WorkspaceType] = mapped_column(
        enum_column(WorkspaceType, "flexdesk_workspace_type"), nullable=False
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    has_monitor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_power: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    has_window: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_quiet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[WorkspaceStatus] = mapped_column(
        enum_column(WorkspaceStatus, "flexdesk_workspace_status"),
        nullable=False,
        default=WorkspaceStatus.AVAILABLE,
        server_default=WorkspaceStatus.AVAILABLE.value,
    )


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "booking_date",
            "start_time",
            "end_time",
            name="uq_booking_window",
        ),
        CheckConstraint("end_time > start_time", name="ck_bookings_valid_time_window"),
        Index("ix_bookings_user_id", "user_id"),
        Index("ix_bookings_workspace_id", "workspace_id"),
        Index("ix_bookings_booking_date", "booking_date"),
        Index("ix_bookings_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        enum_column(BookingStatus, "flexdesk_booking_status"),
        nullable=False,
        default=BookingStatus.CONFIRMED,
        server_default=BookingStatus.CONFIRMED.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )


class Preference(Base):
    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    preferred_type: Mapped[str | None] = mapped_column(String(30))
    preferred_location: Mapped[str | None] = mapped_column(String(120))
    preferred_facilities: Mapped[str | None] = mapped_column(String(255))
    quiet_preference: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )


class LoginHistory(Base):
    __tablename__ = "login_history"
    __table_args__ = (Index("ix_login_history_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    event: Mapped[LoginEvent] = mapped_column(
        enum_column(LoginEvent, "flexdesk_login_event"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
