from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class SMSMFASetupRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number for SMS MFA")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        # If already formatted with +, keep as is
        if v.startswith("+"):
            digits_only = re.sub(r"\D", "", v)
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValueError("Phone number must be between 10 and 15 digits")
            return v

        digits_only = re.sub(r"\D", "", v)

        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError("Phone number must be between 10 and 15 digits")

        # Format as international number
        if len(digits_only) == 10:
            return f"+1{digits_only}"  # Assume US number
        elif digits_only.startswith("1") and len(digits_only) == 11:
            return f"+{digits_only}"
        else:
            return f"+{digits_only}"


class SMSMFAVerifyRequest(BaseModel):
    mfa_code: str = Field(
        ..., description="6-digit MFA code", min_length=6, max_length=6
    )

    @field_validator("mfa_code")
    @classmethod
    def validate_mfa_code(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("MFA code must contain only digits")
        return v


class SMSMFAResponse(BaseModel):
    message: str = Field(..., description="Response message")
    message_id: Optional[str] = Field(None, description="SMS message ID if applicable")


class EmailMFASetupRequest(BaseModel):
    pass


class EmailMFAVerifyRequest(BaseModel):
    mfa_code: str = Field(
        ..., description="6-digit MFA code", min_length=6, max_length=6
    )

    @field_validator("mfa_code")
    @classmethod
    def validate_mfa_code(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("MFA code must contain only digits")
        return v


class EmailMFAResponse(BaseModel):
    message: str = Field(..., description="Response message")
    email: Optional[str] = Field(None, description="Email address if applicable")
