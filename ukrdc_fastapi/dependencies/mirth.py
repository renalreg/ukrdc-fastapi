from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from mirth_client import MirthAPI

from ukrdc_fastapi.config import settings


@asynccontextmanager
async def mirth_session() -> AsyncGenerator[MirthAPI, None]:
    """Connect, login to, and yeild a new MirthAPI session

    Yields:
        [MirthAPI]: MirthAPI session
    """
    async with MirthAPI(
        settings.mirth_url, verify_ssl=settings.mirth_verify_ssl, timeout=None
    ) as api:
        await api.login(settings.mirth_user, settings.mirth_pass)
        yield api
