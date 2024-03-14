from datetime import datetime
import json
import re
from typing import Any, Dict


def get_iso_datetime() -> str:
    return datetime.utcnow().isoformat()[:-3] + "Z"


def to_snake_case(var: str) -> str:
    lower_var = var.lower().strip()
    res = re.sub("\s+", "_", lower_var)
    return res


def to_kebab_case(var: str) -> str:
    lower_var = var.lower().strip()
    res = re.sub("\s+", "-", lower_var)
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
