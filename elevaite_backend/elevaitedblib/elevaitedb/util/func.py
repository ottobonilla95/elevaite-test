from datetime import datetime, UTC
import json
import re
from typing import Any, Dict


def get_iso_datetime() -> str:
    return get_utc_datetime().isoformat()[:-3] + "Z"


def to_snake_case(var: str) -> str:
    lower_var = var.lower().strip()
    res = re.sub("\s+", "_", lower_var)
    return res


def to_kebab_case(var: str) -> str:
    lower_var = var.lower().strip()
    res = re.sub("[\s+_]", "-", lower_var)
    return res


def to_dict(obj: Any) -> Dict[str, Any]:
    return json.loads(
        json.dumps(
            obj,
            default=lambda o: o.__dict__,
            sort_keys=True,
            indent=4,
        )
    )


def get_utc_datetime() -> datetime:
    return datetime.now(UTC)
