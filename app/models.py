from datetime import datetime, timezone
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def utcnow() -> datetime:
    """Наивное UTC-время: SQLite не хранит часовой пояс."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Service(db.Model):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    short_description: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    icon_name: Mapped[str] = mapped_column(String(50), default="spark", nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    leads: Mapped[list["Lead"]] = relationship(
        back_populates="service",
        passive_deletes=True,
    )

    __table_args__ = (Index("ix_services_published_order", "is_published", "sort_order"),)

    def __repr__(self) -> str:  # pragma: no cover - отладочное
        return f"<Service {self.slug}>"


class Project(db.Model):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    summary: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    challenge: Mapped[str] = mapped_column(Text, default="", nullable=False)
    solution: Mapped[str] = mapped_column(Text, default="", nullable=False)
    outcome: Mapped[str] = mapped_column(Text, default="", nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (Index("ix_projects_published_featured", "is_published", "is_featured"),)

    def __repr__(self) -> str:  # pragma: no cover - отладочное
        return f"<Project {self.slug}>"


class Testimonial(db.Model):
    __tablename__ = "testimonials"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_name: Mapped[str] = mapped_column(String(120), nullable=False)
    company_label: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (Index("ix_testimonials_published_order", "is_published", "sort_order"),)

    def __repr__(self) -> str:  # pragma: no cover - отладочное
        return f"<Testimonial {self.author_name}>"


class Lead(db.Model):
    __tablename__ = "leads"

    STATUSES = ("new", "in_progress", "done", "rejected")
    STATUS_LABELS = {
        "new": "Новая",
        "in_progress": "В работе",
        "done": "Закрыта",
        "rejected": "Отклонена",
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact: Mapped[str] = mapped_column(String(160), nullable=False)
    service_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False)

    service: Mapped[Optional["Service"]] = relationship(back_populates="leads")

    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'in_progress', 'done', 'rejected')",
            name="ck_leads_status",
        ),
        Index("ix_leads_status_created", "status", "created_at"),
    )

    @property
    def status_label(self) -> str:
        return self.STATUS_LABELS.get(self.status, self.status)

    def __repr__(self) -> str:  # pragma: no cover - отладочное
        return f"<Lead {self.id} {self.status}>"


class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:  # pragma: no cover - отладочное
        return f"<AdminUser {self.username}>"
