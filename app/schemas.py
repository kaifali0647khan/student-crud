"""Pydantic models = request validation + response shape."""
import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-]{6,14}$")


class StudentFields(BaseModel):
    """All fields optional here; Create makes the mandatory ones required."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[str] = Field(default=None, max_length=254)
    phone: Optional[str] = None
    course: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    enrollment_date: Optional[date] = None

    @field_validator("name", "course", "address")
    @classmethod
    def strip_text(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def valid_dob(cls, v):
        if v is None:
            return v
        if v > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        if v.year < 1900:
            raise ValueError("date_of_birth is too old (before 1900)")
        return v

    @field_validator("email")
    @classmethod
    def valid_email(cls, v):
        if v is None:
            return v
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("invalid email format")
        return v

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not PHONE_RE.match(v):
            raise ValueError("invalid phone number (7-15 digits, optional leading +)")
        return v


class StudentCreate(StudentFields):
    name: str = Field(min_length=2, max_length=100)
    date_of_birth: date

    @model_validator(mode="after")
    def need_contact(self):
        if not self.email and not self.phone:
            raise ValueError("provide at least one contact: email or phone")
        return self


class StudentUpdate(StudentFields):
    """Used by PATCH: send only the fields you want to change."""


class StudentOut(BaseModel):
    id: int
    name: str
    date_of_birth: date
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None
    created_at: str
    updated_at: str


class AIQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AIAnswer(BaseModel):
    question: str
    answer: str
    model: str
    records_used: int
    facts: list[str]
