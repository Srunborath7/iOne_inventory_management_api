import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.domain.auth.model import Auth
from app.domain.auth.schema import AuthCreate, AuthLogin, AuthResponse, TokenResponse
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import (
    AuthService,
    EmailAlreadyRegistered,
    InvalidCredentials,
)


router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> Auth:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized()

    try:
        account_id = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise unauthorized() from None

    account = await AuthRepository(session).get_by_id(account_id)
    if account is None:
        raise unauthorized()
    return account


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: AuthCreate,
    session: AsyncSession = Depends(get_db),
) -> AuthResponse:
    service = AuthService(AuthRepository(session))
    try:
        return await service.register(data)
    except EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from None


@router.post("/login", response_model=TokenResponse)
async def login(
    data: AuthLogin,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(AuthRepository(session))
    try:
        return await service.login(data)
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


@router.get("/me", response_model=AuthResponse)
async def get_me(account: Auth = Depends(get_current_account)) -> Auth:
    return account
