from datetime import datetime
import re


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
