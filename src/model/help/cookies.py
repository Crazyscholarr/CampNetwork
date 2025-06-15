import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from loguru import logger

Base = declarative_base()


class Cookie(Base):
    __tablename__ = "cookies"
    id = Column(Integer, primary_key=True)
    private_key = Column(String, unique=True)
    cf_clearance = Column(String)
    created_at = Column(DateTime)
    expires_at = Column(DateTime)


class CookieDatabase:
    def __init__(self):
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///data/cookies.db",
            echo=False,
        )
        self.session = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Initialize the cookie database"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.success("Cookie database initialized successfully")

    async def clear_database(self):
        """Clear the cookie database"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        logger.success("Cookie database cleared successfully")

    async def save_cookie(
        self, private_key: str, cf_clearance: str, expiration_hours: float = 25 / 60
    ) -> None:
        """
        Save a Cloudflare clearance cookie for a wallet

        :param private_key: Private key of the wallet
        :param cf_clearance: Cloudflare clearance cookie value
        :param expiration_hours: Cookie expiration time in hours (default: 25 minutes)
        """
        now = datetime.now()
        expires_at = now + timedelta(hours=expiration_hours)

        async with self.session() as session:
            # Check if the cookie already exists for this wallet
            existing_cookie = await self._get_cookie(session, private_key)

            if existing_cookie:
                # Update existing cookie
                existing_cookie.cf_clearance = cf_clearance
                existing_cookie.created_at = now
                existing_cookie.expires_at = expires_at
                logger.info(
                    f"Updated cookie for wallet {private_key[:4]}...{private_key[-4:]}"
                )
            else:
                # Create new cookie entry
                cookie = Cookie(
                    private_key=private_key,
                    cf_clearance=cf_clearance,
                    created_at=now,
                    expires_at=expires_at,
                )
                session.add(cookie)
                logger.info(
                    f"Saved new cookie for wallet {private_key[:4]}...{private_key[-4:]}"
                )

            await session.commit()

    async def get_valid_cookie(self, private_key: str) -> Optional[str]:
        """
        Get a valid Cloudflare clearance cookie for a wallet

        :param private_key: Private key of the wallet
        :return: Cloudflare clearance cookie value if valid, None otherwise
        """
        async with self.session() as session:
            cookie = await self._get_cookie(session, private_key)

            if not cookie:
                logger.info(
                    f"No cookie found for wallet {private_key[:4]}...{private_key[-4:]}"
                )
                return None

            # Check if the cookie is still valid
            if cookie.expires_at < datetime.now():
                logger.info(
                    f"Cookie expired for wallet {private_key[:4]}...{private_key[-4:]}"
                )
                return None

            logger.info(
                f"Using valid cookie for wallet {private_key[:4]}...{private_key[-4:]}"
            )
            return cookie.cf_clearance

    async def delete_cookie(self, private_key: str) -> bool:
        """
        Delete a cookie for a wallet

        :param private_key: Private key of the wallet
        :return: True if deleted, False if not found
        """
        async with self.session() as session:
            cookie = await self._get_cookie(session, private_key)

            if not cookie:
                logger.info(
                    f"No cookie to delete for wallet {private_key[:4]}...{private_key[-4:]}"
                )
                return False

            await session.delete(cookie)
            await session.commit()
            logger.info(
                f"Deleted cookie for wallet {private_key[:4]}...{private_key[-4:]}"
            )
            return True

    async def delete_expired_cookies(self) -> int:
        """
        Delete all expired cookies

        :return: Number of deleted cookies
        """
        from sqlalchemy import delete

        async with self.session() as session:
            query = delete(Cookie).where(Cookie.expires_at < datetime.now())
            result = await session.execute(query)
            await session.commit()

            count = result.rowcount
            logger.info(f"Deleted {count} expired cookies")
            return count

    async def get_all_cookies(self) -> Dict:
        """
        Get all cookies with their information

        :return: Dictionary mapping private keys to cookie information
        """
        from sqlalchemy import select

        async with self.session() as session:
            query = select(Cookie)
            result = await session.execute(query)
            cookies = result.scalars().all()

            return {
                cookie.private_key: {
                    "cf_clearance": cookie.cf_clearance,
                    "created_at": cookie.created_at.isoformat(),
                    "expires_at": cookie.expires_at.isoformat(),
                    "is_valid": cookie.expires_at > datetime.now(),
                }
                for cookie in cookies
            }

    async def get_cookie_info(self, private_key: str) -> Optional[Dict]:
        """
        Get information about a cookie

        :param private_key: Private key of the wallet
        :return: Cookie information or None if not found
        """
        async with self.session() as session:
            cookie = await self._get_cookie(session, private_key)

            if not cookie:
                return None

            return {
                "cf_clearance": cookie.cf_clearance,
                "created_at": cookie.created_at.isoformat(),
                "expires_at": cookie.expires_at.isoformat(),
                "is_valid": cookie.expires_at > datetime.now(),
                "time_left": (
                    (cookie.expires_at - datetime.now()).total_seconds() / 3600
                    if cookie.expires_at > datetime.now()
                    else 0
                ),
            }

    async def _get_cookie(
        self, session: AsyncSession, private_key: str
    ) -> Optional[Cookie]:
        """Internal method to get a cookie by private key"""
        from sqlalchemy import select

        result = await session.execute(
            select(Cookie).filter_by(private_key=private_key)
        )
        return result.scalar_one_or_none()
