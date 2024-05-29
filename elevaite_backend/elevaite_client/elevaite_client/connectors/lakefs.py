import os
from typing import Dict, Literal
import lakefs

KEY_ID = "key_id"


def get_or_create_lakefs_repo(
    repo_name: str,
    options: Dict[
        Literal["key_id"]
        | Literal["secret_key"]
        | Literal["endpoint"]
        | Literal["namespace"],
        str | None,
    ],
) -> lakefs.Repository:
    LAKEFS_ACCESS_KEY_ID = (
        options["key_id"]
        if options["key_id"] is not None
        else os.getenv("LAKEFS_ACCESS_KEY_ID")
    )
    LAKEFS_SECRET_ACCESS_KEY = (
        options["secret_key"]
        if options["secret_key"] is not None
        else os.getenv("LAKEFS_SECRET_ACCESS_KEY")
    )
    LAKEFS_ENDPOINT_URL = (
        options["endpoint"]
        if options["endpoint"] is not None
        else os.getenv("LAKEFS_ENDPOINT_URL")
    )
    LAKEFS_STORAGE_NAMESPACE = (
        options["namespace"]
        if options["namespace"] is not None
        else os.getenv("LAKEFS_STORAGE_NAMESPACE")
    )
    if LAKEFS_ACCESS_KEY_ID is None:
        raise Exception("LAKEFS_ACCESS_KEY_ID is null")
    if LAKEFS_SECRET_ACCESS_KEY is None:
        raise Exception("LAKEFS_SECRET_ACCESS_KEY is null")
    if LAKEFS_ENDPOINT_URL is None:
        raise Exception("LAKEFS_ENDPOINT_URL is null")
    if LAKEFS_STORAGE_NAMESPACE is None:
        raise Exception("LAKEFS_STORAGE_NAMESPACE is null")

    clt = lakefs.Client(
        host=LAKEFS_ENDPOINT_URL,
        username=LAKEFS_ACCESS_KEY_ID,
        password=LAKEFS_SECRET_ACCESS_KEY,
    )
    repo = None

    for _repo in lakefs.repositories(client=clt):
        if _repo.id == repo_name:
            repo = _repo
            break
    if repo is None:
        repo = lakefs.Repository(repo_name, client=clt).create(
            storage_namespace=f"s3://{LAKEFS_STORAGE_NAMESPACE}/{repo_name}"
        )

    return repo
