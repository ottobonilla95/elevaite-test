"""Token schemas."""

from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """Token schema."""

    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: str
    exp: int
    type: str = "access"

    # Configuration
    model_config: ClassVar[ConfigDict] = ConfigDict(
        strict=True,
        json_schema_extra={
            "example": {
                "sub": "123",
                "exp": 1516239022,
                "type": "access",
            }
        },
    )
