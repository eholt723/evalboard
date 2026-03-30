from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.db.base import Base  # noqa: F401 — re-exported for convenience


def _parse_db_url(url: str) -> tuple[str, bool]:
    """Return (asyncpg URL with no query params, ssl_required bool)."""
    from urllib.parse import urlparse, urlunparse, parse_qs
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            url = "postgresql+asyncpg://" + url[len(prefix):]
            break
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    ssl_required = params.get("sslmode", ["disable"])[0] in ("require", "verify-ca", "verify-full")
    clean_url = urlunparse(parsed._replace(query=""))
    return clean_url, ssl_required


_db_url, _ssl = _parse_db_url(settings.database_url)
engine = create_async_engine(
    _db_url,
    echo=False,
    connect_args={"ssl": True} if _ssl else {},
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
