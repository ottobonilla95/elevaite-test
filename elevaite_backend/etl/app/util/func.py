from datetime import datetime


def get_iso_datetime() -> str:
    return datetime.utcnow().isoformat()[:-3] + "Z"


def get_routing_key(application_id: int) -> str:
    match application_id:
        case 1:
            return "s3_ingest"
        case 2:
            return "preprocess"
        case _:
            return "default"
