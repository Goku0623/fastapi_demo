from redis import asyncio
from src.config import Config

JTI_EXPIRY = 3600

token_blacklist = asyncio.from_url(Config.REDIS_URL)

async def add_jti_to_blacklist(jti: str) -> None:
    await token_blacklist.set(
        name=jti,
        value="blacklisted",
        ex=JTI_EXPIRY
    )


async def token_in_blacklist(jti: str) -> bool:
    result = await token_blacklist.get(jti)
    return result is not None