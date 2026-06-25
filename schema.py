from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class UserBase(BaseModel):
    first_name: str = Field(min_length=2, max_length=20)
    last_name: str = Field(min_length=2, max_length=20)
    username: str = Field(min_length=7, max_length=30)


class UserCreate(UserBase):
    password: str = Field(min_length=7)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(default=None, min_length=2, max_length=20)
    last_name: str | None = Field(default=None, min_length=2, max_length=20)
    username: str | None = Field(default=None, min_length=7, max_length=30)


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=7)
    new_password: str = Field(min_length=7)

    @model_validator(mode="after")
    def verify_passwords(self):
        if self.current_password == self.new_password:
            raise ValueError("New password must not match current password")

        return self


# ===================================================================================


class Status(str, Enum):
    PENDING = "pending"
    INPROCESS = "inprocess"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class ApplicationAgeFilter(str, Enum):
    YESTERDAY = "yesterday"
    LAST_WEEK = "last_week"
    LAST_2WEEKS = "last_2weeks"
    LAST_MONTH = "last_month"


class ApplicationBase(BaseModel):
    company_name: str = Field(min_length=1, max_length=30)
    job_title: str = Field(min_length=5, max_length=30)
    status: Status
    applied_date: date = Field(default_factory=date.today)

    @field_validator("applied_date")
    @classmethod
    def validate_date(cls, v: date):
        if v > date.today():
            raise ValueError("Applied date must not be in future")
        return v


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationResponse(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID


class ApplicationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str | None = Field(default=None, min_length=1, max_length=30)
    job_title: str | None = Field(default=None, min_length=5, max_length=30)
    applied_date: date | None = Field(default=None)
    status: Status | None = Field(default=None)

    @field_validator("applied_date")
    @classmethod
    def validate_date(cls, v: date):
        if v > date.today():
            raise ValueError("Applied date must not be in future")
        return v


class ApplicationPageResponse(BaseModel):
    items: list[ApplicationResponse]
    count: int
    limit: int
    page: int
