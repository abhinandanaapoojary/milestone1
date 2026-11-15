import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    BigInteger, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import SubmissionStatus
from app.models.mixins import UUIDPrimaryKeyMixin


class Submission(UUIDPrimaryKeyMixin, Base):
    """
    One respondent's attempt at a form version.
    started_at / submitted_at / status power the analytics
    (completion rate = submitted / started, average time to complete).
    """

    __tablename__ = "submissions"

    form_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("form_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status", values_callable=lambda e: [m.value for m in e]),
        default=SubmissionStatus.STARTED, nullable=False, index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    respondent_ip: Mapped[Optional[str]] = mapped_column(String(45))

    form_version: Mapped["FormVersion"] = relationship(back_populates="submissions")  # noqa: F821
    values: Mapped[List["ResponseValue"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )


class ResponseValue(UUIDPrimaryKeyMixin, Base):
    """
    One answer to one field. Typed value columns keep filtering/aggregation fast;
    only the column matching the field type is filled.
      text/email/dropdown -> value_text   | number/rating -> value_number
      date                -> value_date   | checkbox       -> value_json (list)
      file                -> file_* columns
    """

    __tablename__ = "response_values"
    __table_args__ = (UniqueConstraint("submission_id", "field_id", name="uq_one_value_per_field"),)

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value_text: Mapped[Optional[str]] = mapped_column(Text)
    value_number: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6))
    value_date: Mapped[Optional[date]] = mapped_column(Date)
    value_json: Mapped[Optional[list]] = mapped_column(JSONB)
    file_name: Mapped[Optional[str]] = mapped_column(String(255))
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    file_content_type: Mapped[Optional[str]] = mapped_column(String(100))

    submission: Mapped["Submission"] = relationship(back_populates="values")
    field: Mapped["Field"] = relationship()  # noqa: F821


from app.models.form import FormVersion  # noqa: E402,F401
from app.models.field import Field  # noqa: E402,F401
