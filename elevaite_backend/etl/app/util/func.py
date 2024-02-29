from datetime import datetime


def get_iso_datetime() -> str:
    return datetime.utcnow().isoformat()[:-3] + "Z"
