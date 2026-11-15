"""Inserts one sample form (with options, a conditional rule, a submission) to prove the schema works.
Run from project root:  python -m scripts.seed_sample
"""
import secrets
from datetime import datetime, timezone

from app.database.session import SessionLocal
from app.models import (
    ConditionalRule, ConditionOperator, Field, FieldOption, FieldType, Form, FormStatus,
    FormVersion, ResponseValue, RuleAction, Submission, SubmissionStatus,
)


def main() -> None:
    db = SessionLocal()
    try:
        form = Form(title="Employee Feedback", description="Sample form", owner_id="demo-user")
        version = FormVersion(
            form=form, version_number=1, status=FormStatus.PUBLISHED,
            share_token=secrets.token_urlsafe(16), published_at=datetime.now(timezone.utc),
        )
        name = Field(form_version=version, field_key="name", label="Full name",
                     field_type=FieldType.TEXT, is_required=True, position=1,
                     config={"min_length": 2, "max_length": 100})
        status = Field(form_version=version, field_key="status", label="Employment status",
                       field_type=FieldType.DROPDOWN, is_required=True, position=2)
        status.options = [FieldOption(label="Employed", value="employed", position=1),
                          FieldOption(label="Student", value="student", position=2)]
        company = Field(form_version=version, field_key="company", label="Company name",
                        field_type=FieldType.TEXT, position=3)
        rating = Field(form_version=version, field_key="rating", label="Rate us",
                       field_type=FieldType.RATING, position=4, config={"scale": 5})
        rule = ConditionalRule(form_version=version, trigger_field=status, operator=ConditionOperator.EQUALS,
                               comparison_value="employed", target_field=company, action=RuleAction.SHOW)
        sub = Submission(form_version=version, status=SubmissionStatus.SUBMITTED,
                         submitted_at=datetime.now(timezone.utc), duration_seconds=42)
        sub.values = [
            ResponseValue(field=name, value_text="Krupashree"),
            ResponseValue(field=status, value_text="employed"),
            ResponseValue(field=company, value_text="ABC Tech"),
            ResponseValue(field=rating, value_number=5),
        ]
        db.add_all([form, version, name, status, company, rating, rule, sub])
        db.commit()
        print("Seed OK. Form id:", form.id, "| share token:", version.share_token)
    finally:
        db.close()


if __name__ == "__main__":
    main()
