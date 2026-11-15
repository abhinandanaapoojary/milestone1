import uuid
from typing import List, Optional

from sqlalchemy import (
    Boolean, CheckConstraint, Enum, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ConditionOperator, FieldType, RuleAction
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


def _enum(enum_cls, name):
    return Enum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e])


class Field(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A question on a form version.
    `config` holds per-type validation constraints, e.g.
      text:   {"min_length": 2, "max_length": 100}
      number: {"min": 0, "max": 100, "integer_only": true}
      date:   {"min_date": "2024-01-01", "max_date": "2030-12-31"}
      file:   {"allowed_types": ["pdf", "png"], "max_size_mb": 5}
      rating: {"scale": 5}
    """

    __tablename__ = "fields"
    __table_args__ = (
        UniqueConstraint("form_version_id", "field_key", name="uq_field_key_per_version"),
    )

    form_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("form_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)  # stable machine name
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[FieldType] = mapped_column(_enum(FieldType, "field_type"), nullable=False)
    placeholder: Mapped[Optional[str]] = mapped_column(String(255))
    help_text: Mapped[Optional[str]] = mapped_column(Text)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    form_version: Mapped["FormVersion"] = relationship(back_populates="fields")  # noqa: F821
    options: Mapped[List["FieldOption"]] = relationship(
        back_populates="field", cascade="all, delete-orphan", order_by="FieldOption.position"
    )


class FieldOption(UUIDPrimaryKeyMixin, Base):
    """Choices for dropdown / multi-checkbox fields."""

    __tablename__ = "field_options"
    __table_args__ = (UniqueConstraint("field_id", "value", name="uq_option_value_per_field"),)

    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    field: Mapped["Field"] = relationship(back_populates="options")


class ConditionalRule(UUIDPrimaryKeyMixin, Base):
    """
    "If <trigger_field> <operator> <comparison_value> then <action> <target_field>".
    Example: if `employment_status` equals "employed" then show `company_name`.
    """

    __tablename__ = "conditional_rules"
    __table_args__ = (
        CheckConstraint("trigger_field_id <> target_field_id", name="ck_rule_trigger_not_target"),
    )

    form_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("form_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger_field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"), nullable=False
    )
    operator: Mapped[ConditionOperator] = mapped_column(
        _enum(ConditionOperator, "condition_operator"), nullable=False
    )
    comparison_value: Mapped[Optional[str]] = mapped_column(String(255))  # NULL for is_empty
    target_field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[RuleAction] = mapped_column(_enum(RuleAction, "rule_action"), nullable=False)

    form_version: Mapped["FormVersion"] = relationship(back_populates="rules")  # noqa: F821
    trigger_field: Mapped["Field"] = relationship(foreign_keys=[trigger_field_id])
    target_field: Mapped["Field"] = relationship(foreign_keys=[target_field_id])
