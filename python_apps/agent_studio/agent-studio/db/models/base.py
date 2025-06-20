
import uuid
from datetime import UTC, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    Float,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship, remote, foreign

from ..database import Base

def get_utc_datetime() -> datetime:
    return datetime.now(UTC)
