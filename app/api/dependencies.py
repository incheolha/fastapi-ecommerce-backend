
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApiException
from app.core.security import decode_access_token
from app.db.database import db_session
from app.models.user import User, UserRole


http_bearer = HTTPBearer();


async def get_current_user(
    db: AsyncSession = Depends(db_session),
    token: HTTPAuthorizationCredentials = Depends(http_bearer),   #자동으로 http header검토후 jwt내용을 가져온다 token.schema 와 token.credential을 return한다
) -> User:
    # 1. Decode the token
    payload = decode_access_token(token.credentials) # payload리턴값은 sub, iat, exp를 준다
    user_id: str | None = payload.get("sub")

    if not user_id:
        raise ApiException(
            "Could not validate credentials", status.HTTP_401_UNAUTHORIZED
        )

    # 2. Get user from DB using primary key lookup
    user = await db.get(User, int(user_id))

    if not user:
        raise ApiException("User not found", status.HTTP_404_NOT_FOUND)

    if not user.active:
        raise ApiException("User is inactive", status.HTTP_400_BAD_REQUEST)

    return user    # 찿은후 리턴값을 user data를 준다



async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ApiException(
            "You do not have administrative privileges",
            status.HTTP_403_FORBIDDEN,
        )

    return current_user



async def get_current_admin_or_delivery(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.DELIVERY):
        raise ApiException(
            "You do not have permission to access this resource",
            status.HTTP_403_FORBIDDEN,
        )
    return current_user