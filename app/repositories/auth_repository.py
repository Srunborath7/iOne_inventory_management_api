from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.model import Auth


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Auth | None:
        result = await self.session.execute(select(Auth).where(Auth.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, account_id: int) -> Auth | None:
        result = await self.session.execute(select(Auth).where(Auth.id == account_id))
        return result.scalar_one_or_none()

    async def create(self, *, full_name: str, email: str, password_hash: str) -> Auth:
        account = Auth(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
        )
        self.session.add(account)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(account)
        return account
