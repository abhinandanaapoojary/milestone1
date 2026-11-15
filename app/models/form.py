import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import FormStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Form(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A form owned by a user. The actual structure lives in FormVersion."""

    __tablename__ = "forms"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)  # placeholder until auth module exists
    status: Mapped[FormStatus] = mapped_column(
        Enum(FormStatus, name="form_status", values_callable=lambda e: [m.value for m in e]),
        default=FormStatus.DRAFT, nullable=False, index=True,
    )

    versions: Mapped[List["FormVersion"]] = relationship(
        back_populates="form", cascade="all, delete-orphan", order_by="FormVersion.version_number"
    )


class FormVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    An immutable-once-published snapshot of a form's structure.
    Editing a published form creates a NEW version; submissions stay linked to the
    version they were made against.
    """

    __tablename__ = "form_versions"
    __table_args__ = (UniqueConstraint("form_id", "version_number", name="uq_form_version_number"),)

    form_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[FormStatus] = mapped_column(
        Enum(FormStatus, name="form_status", values_callable=lambda e: [m.value for m in e]),
        default=FormStatus.DRAFT, nullable=False,
    )
    share_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)  # shareable link
    schema_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)  # frozen schema at publish time
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    form: Mapped["Form"] = relationship(back_populates="versions")
    fields: Mapped[List["Field"]] = relationship(
        back_populates="form_version", cascade="all, delete-orphan", order_by="Field.position"
    )
    rules: Mapped[List["ConditionalRule"]] = relationship(
        back_populates="form_version", cascade="all, delete-orphan"
    )
    submissions: Mapped[List["Submission"]] = relationship(back_populates="form_version")


from app.models.field import ConditionalRule, Field  # noqa: E402
from app.models.submission import Submission  # noqa: E402
