from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from security import clean_text, normalize_email


class CustomerInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    company: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=30)

    @field_validator("name", "company", "phone", mode="before")
    @classmethod
    def sanitize_text_fields(cls, value):
        if value is None:
            return None
        return clean_text(value, 120, allow_newlines=False)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, value):
        return normalize_email(str(value))


class LeadInput(BaseModel):
    email: EmailStr
    requirement: str = Field(min_length=3, max_length=1000)
    company_size: int | None = Field(default=None, ge=1, le=1_000_000)
    budget_usd: float | None = Field(default=None, ge=0, le=1_000_000_000)
    timeline_days: int | None = Field(default=None, ge=1, le=3650)
    decision_maker: bool | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, value):
        return normalize_email(str(value))

    @field_validator("requirement", mode="before")
    @classmethod
    def sanitize_requirement(cls, value):
        return clean_text(value, 1000)


class MeetingInput(BaseModel):
    email: EmailStr
    preferred_time: str = Field(min_length=2, max_length=120)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, value):
        return normalize_email(str(value))

    @field_validator("preferred_time", "notes", mode="before")
    @classmethod
    def sanitize_text_fields(cls, value):
        if value is None:
            return None
        return clean_text(value, 500, allow_newlines=False)
