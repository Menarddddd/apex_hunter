from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


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


class Status(Enum):
    pending = "pending"
    inprocess = "inprocess"
    rejected = "rejected"
    passed = "passed"


class ApplicationBase(BaseModel):
    company_name: str = Field(min_length=1, max_length=30)
    job_title: str = Field(min_length=5, max_length=30)
    status: Status
    applied_date: date = Field(default=date.today())


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationResponse(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)


class ApplicationUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=30)
    job_title: str | None = Field(default=None, min_length=5, max_length=30)
    applied_date: date | None = Field(default=None)


class ApplicationStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Status
