from typing import Optional


def build_db_uri(
    driver: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    name: Optional[str] = None,
):
    if driver == "sqlite":
        return f"{driver}:///{name}"
    else:
        return f"{driver}://{user}:{password}@{host}:{port}/{name}"
