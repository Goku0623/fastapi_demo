from fastapi.security import HTTPBearer
from fastapi.exceptions import HTTPException
from fastapi import Request, status, Depends
from .utils import decode_token
from .service import UserService
from src.db.models import User
from src.db.redis import token_in_blacklist
from src.db.main import get_session
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio.session import AsyncSession
from typing import Any, List
from src.errors import (
    InvalidToken,
    RefreshTokenRequired,
    AccessTokenRequired,
    InsufficientPermission,
    AccountNotVerified,
)


user_service =  UserService()

class TokenBear(HTTPBearer):
    def __init__(self, auto_error = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        creds = await super().__call__(request)
        token = creds.credentials
        token_data = decode_token(token)

        if not self.token_valid(token):
            raise InvalidToken()
        
        if await token_in_blacklist(token_data["jti"]):
            raise InvalidToken()
        
        # 记得调用
        self.verify_token_data(token_data)
        return token_data 
    
    def token_valid(self, token: str) -> bool:
        token_data = decode_token(token)
        return token_data is not None

    def verify_token_data(self, token_data):
        raise(NotImplementedError("请在子类中覆盖此方法！"))

    
class AccessTokenBear(TokenBear):
    # 需要的是访问令牌，而不是刷新令牌（刷新令牌也可以通过校验）
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data["refresh"]:
            raise AccessTokenRequired()


class RefreshTokenBear(TokenBear):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data["refresh"]:
            raise RefreshTokenRequired()


async def get_current_user(
    token_details: dict = Depends(AccessTokenBear()),
    session: AsyncSession = Depends(get_session)
):
    email = token_details["user"]["email"]
    user = await user_service.get_user_by_email(email, session)
    return user


class RoleChecker:

    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> Any:
        if not current_user.is_verified:
            raise AccountNotVerified()
        if current_user.role in self.allowed_roles:
            return True
        raise InsufficientPermission()