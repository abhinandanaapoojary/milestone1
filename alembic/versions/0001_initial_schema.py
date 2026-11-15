"""initial schema: forms, versions, fields, options, rules, submissions, responses

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False -> we create/drop the types explicitly below (so they can be shared by tables)
form_status = pg.ENUM("draft", "published", "archived", name="form_status", create_type=False)
field_type = pg.ENUM(
    "text", "number", "email", "dropdown", "checkbox", "date", "file", "rating",
    name="field_type", create_type=False,
)
condition_operator = pg.ENUM(
    "equals", "not_equals", "contains", "greater_than", "is_empty",
    name="condition_operator", create_type=False,
)
rule_action = pg.ENUM("show", "hide", "require", name="rule_action", create_type=False)
submission_status = pg.ENUM("started", "submitted", name="submission_status", create_type=False)

ALL_ENUMS = [form_status, field_type, condition_operator, rule_action, submission_status]


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    for e in ALL_ENUMS:
        e.create(bind, checkfirst=True)

    op.create_table(
        "forms",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("owner_id", sa.String(100)),
        sa.Column("status", form_status, nullable=False, server_default="draft"),
        *_ts(),
    )
    op.create_index("ix_forms_owner_id", "forms", ["owner_id"])
    op.create_index("ix_forms_status", "forms", ["status"])

    op.create_table(
        "form_versions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("form_id", pg.UUID(as_uuid=True), sa.ForeignKey("forms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", form_status, nullable=False, server_default="draft"),
        sa.Column("share_token", sa.String(64)),
        sa.Column("schema_snapshot", pg.JSONB()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        *_ts(),
        sa.UniqueConstraint("form_id", "version_number", name="uq_form_version_number"),
    )
    op.create_index("ix_form_versions_form_id", "form_versions", ["form_id"])
    op.create_index("ix_form_versions_share_token", "form_versions", ["share_token"], unique=True)

    op.create_table(
        "fields",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("form_version_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("form_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_key", sa.String(100), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("field_type", field_type, nullable=False),
        sa.Column("placeholder", sa.String(255)),
        sa.Column("help_text", sa.Text()),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("config", pg.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts(),
        sa.UniqueConstraint("form_version_id", "field_key", name="uq_field_key_per_version"),
    )
    op.create_index("ix_fields_form_version_id", "fields", ["form_version_id"])

    op.create_table(
        "field_options",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("field_id", pg.UUID(as_uuid=True), sa.ForeignKey("fields.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("value", sa.String(255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("field_id", "value", name="uq_option_value_per_field"),
    )
    op.create_index("ix_field_options_field_id", "field_options", ["field_id"])

    op.create_table(
        "conditional_rules",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("form_version_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("form_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trigger_field_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("fields.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operator", condition_operator, nullable=False),
        sa.Column("comparison_value", sa.String(255)),
        sa.Column("target_field_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("fields.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", rule_action, nullable=False),
        sa.CheckConstraint("trigger_field_id <> target_field_id", name="ck_rule_trigger_not_target"),
    )
    op.create_index("ix_conditional_rules_form_version_id", "conditional_rules", ["form_version_id"])

    op.create_table(
        "submissions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("form_version_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("form_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", submission_status, nullable=False, server_default="started"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("respondent_ip", sa.String(45)),
    )
    op.create_index("ix_submissions_form_version_id", "submissions", ["form_version_id"])
    op.create_index("ix_submissions_status", "submissions", ["status"])
    op.create_index("ix_submissions_submitted_at", "submissions", ["submitted_at"])

    op.create_table(
        "response_values",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_id", pg.UUID(as_uuid=True), sa.ForeignKey("fields.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value_text", sa.Text()),
        sa.Column("value_number", sa.Numeric(20, 6)),
        sa.Column("value_date", sa.Date()),
        sa.Column("value_json", pg.JSONB()),
        sa.Column("file_name", sa.String(255)),
        sa.Column("file_path", sa.String(500)),
        sa.Column("file_size_bytes", sa.BigInteger()),
        sa.Column("file_content_type", sa.String(100)),
        sa.UniqueConstraint("submission_id", "field_id", name="uq_one_value_per_field"),
    )
    op.create_index("ix_response_values_submission_id", "response_values", ["submission_id"])
    op.create_index("ix_response_values_field_id", "response_values", ["field_id"])


def downgrade() -> None:
    op.drop_table("response_values")
    op.drop_table("submissions")
    op.drop_table("conditional_rules")
    op.drop_table("field_options")
    op.drop_table("fields")
    op.drop_table("form_versions")
    op.drop_table("forms")
    bind = op.get_bind()
    for e in reversed(ALL_ENUMS):
        e.drop(bind, checkfirst=True)
