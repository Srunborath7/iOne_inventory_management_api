import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
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
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> Auth:
    token: str | None = None

    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise unauthorized()

    try:
        account_id = decode_access_token(token)
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
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(AuthRepository(session))
    try:
        token_data = await service.login(data)
        # Store JWT in HttpOnly cookie for browser sessions
        response.set_cookie(
            key="access_token",
            value=token_data.access_token,
            max_age=token_data.expires_in,
            httponly=True,
            samesite="lax",
            secure=False,
        )
        return token_data
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=AuthResponse)
async def get_me(account: Auth = Depends(get_current_account)) -> Auth:
    return account
