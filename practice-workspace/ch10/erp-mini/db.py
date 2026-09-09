from pathlib import Path
from urllib.parse import urlparse

import pg8000.dbapi
from dotenv import dotenv_values


LOCAL_ENV = Path(__file__).with_name(".env")


def get_connection():
    database_url = str(dotenv_values(LOCAL_ENV).get("DATABASE_URL") or "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    url = urlparse(database_url)
    if not all((url.username, url.password, url.hostname, url.path.lstrip("/"))):
        raise RuntimeError("DATABASE_URL format is invalid")

    return pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        database=url.path.lstrip("/"),
        port=url.port or 5432,
    )
