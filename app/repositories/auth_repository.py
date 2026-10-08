from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.model import Auth


class AuthRepository:
    """Repository handling database operations for Auth entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, account_id: int) -> Auth | None:
        """Find an account by ID."""
        return await self.session.get(Auth, account_id)

    async def get_by_id(self, account_id: int) -> Auth | None:
        """Find an account by ID (alias for get)."""
        return await self.get(account_id)

    async def get_by_email(self, email: str) -> Auth | None:
        """Find an account by email."""
        result = await self.session.execute(select(Auth).where(Auth.email == email))
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        full_name: str,
        email: str,
        password_hash: str,
    ) -> Auth:
        """Create a new user account record."""
        auth = Auth(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
        )
        self.session.add(auth)
        await self._commit()
        await self.session.refresh(auth)
        return auth

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
