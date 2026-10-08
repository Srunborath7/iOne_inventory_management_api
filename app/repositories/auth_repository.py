from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.model import Auth
from app.repositories.base import BaseRepository


class AuthRepository(BaseRepository[Auth]):
    """Repository handling database operations for Auth entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Auth)

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
        return await super().create(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
        )
