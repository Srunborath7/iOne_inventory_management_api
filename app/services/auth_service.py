import hashlib
import hmac
import secrets

from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.security import create_access_token
from app.domain.auth.model import Auth
from app.domain.auth.schema import AuthCreate, AuthLogin, TokenResponse
from app.repositories.auth_repository import AuthRepository


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
    pass


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived_key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt$16384$8$1${salt.hex()}${derived_key.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, expected_hex = encoded_hash.split("$")
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
        )
        return hmac.compare_digest(actual.hex(), expected_hex)
    except (ValueError, TypeError):
        return False


class AuthService:
    def __init__(self, repository: AuthRepository):
        self.repository = repository

    async def register(self, data: AuthCreate) -> Auth:
        email = data.email.strip().lower()
        if await self.repository.get_by_email(email):
            raise EmailAlreadyRegistered

        try:
            return await self.repository.create(
                full_name=data.full_name.strip(),
                email=email,
                password_hash=hash_password(data.password),
            )
        except IntegrityError as exc:
            # The unique database constraint also protects concurrent requests.
            raise EmailAlreadyRegistered from exc

    async def login(self, data: AuthLogin) -> TokenResponse:
        account = await self.repository.get_by_email(data.email.strip().lower())
        if account is None or not verify_password(data.password, account.password_hash):
            raise InvalidCredentials

        return TokenResponse(
            access_token=create_access_token(account.id),
            expires_in=settings.access_token_expire_minutes * 60,
        )
