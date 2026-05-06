from typing import Any, Callable
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi import FastAPI, status
from sqlalchemy.exc import SQLAlchemyError

class BooklyException(Exception):
    """关于bookly应用的基础异常类, 所有自定义异常都应该继承自这个类"""

    pass


class InvalidToken(BooklyException):
    """用户提供了无效或者已过期的令牌"""

    pass


class RevokedToken(BooklyException):
    """用户提供了已被撤销的令牌"""

    pass


class AccessTokenRequired(BooklyException):
    """用户在需要访问令牌时提供了刷新令牌"""

    pass


class RefreshTokenRequired(BooklyException):
    """用户在需要刷新令牌时提供了访问令牌"""

    pass


class UserAlreadyExists(BooklyException):
    """用户在注册时提供了已存在的邮箱"""

    pass


class InvalidCredentials(BooklyException):
    """用户在登录时提供了错误的邮箱或密码"""

    pass


class InsufficientPermission(BooklyException):
    """用户没有执行该操作所需的必要权限"""

    pass


class BookNotFound(BooklyException):
    """书籍未找到"""

    pass


class TagNotFound(BooklyException):
    """标签未找到"""

    pass


class TagAlreadyExists(BooklyException):
    """标签已存在"""

    pass


class UserNotFound(BooklyException):
    """用户未找到"""

    pass


class AccountNotVerified(Exception):
    """用户账户未验证"""
    pass

def create_exception_handler(
    status_code: int, 
    initial_detail: Any
) -> Callable[[Request, Exception], JSONResponse]:

    async def exception_handler(request: Request, exc: BooklyException):
        return JSONResponse(content=initial_detail, status_code=status_code)

    return exception_handler


def register_all_errors(app: FastAPI):
    app.add_exception_handler(
        UserAlreadyExists,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                "message": "用户邮箱已存在",
                "error_code": "user_exists",
            },
        ),
    )

    app.add_exception_handler(
        UserNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                "message": "用户未找到",
                "error_code": "user_not_found",
            },
        ),
    )
    app.add_exception_handler(
        BookNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                "message": "书籍未找到",
                "error_code": "book_not_found",
            },
        ),
    )
    app.add_exception_handler(
        InvalidCredentials,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "无效的邮箱或密码",
                "error_code": "invalid_email_or_password",
            },
        ),
    )
    app.add_exception_handler(
        InvalidToken,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "token无效或已过期",
                "resolution": "请获取新token",
                "error_code": "invalid_token",
            },
        ),
    )
    app.add_exception_handler(
        RevokedToken,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "Token无效或已被撤销",
                "resolution": "请获取新token",
                "error_code": "token_revoked",
            },
        ),
    )
    app.add_exception_handler(
        AccessTokenRequired,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "请提供有效的访问令牌",
                "resolution": "请获取访问令牌",
                "error_code": "access_token_required",
            },
        ),
    )
    app.add_exception_handler(
        RefreshTokenRequired,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                "message": "请提供有效的刷新令牌",
                "resolution": "请获取刷新令牌",
                "error_code": "refresh_token_required",
            },
        ),
    )
    app.add_exception_handler(
        InsufficientPermission,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "您没有执行此操作所需的足够权限",
                "error_code": "insufficient_permissions",
            },
        ),
    )
    app.add_exception_handler(
        TagNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={"message": "标签未找到", "error_code": "tag_not_found"},
        ),
    )

    app.add_exception_handler(
        TagAlreadyExists,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                "message": "标签已存在",
                "error_code": "tag_exists",
            },
        ),
    )

    app.add_exception_handler(
        BookNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                "message": "书籍未找到",
                "error_code": "book_not_found",
            },
        ),
    )

    app.add_exception_handler(
        AccountNotVerified,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                "message": "用户账户未验证",
                "error_code": "account_not_verified",
                "resolution":"请检查您的邮箱并点击验证链接",
            },
        ),
    )

    @app.exception_handler(500)
    async def internal_server_error(request, exc):

        return JSONResponse(
            content={
                "message": "Oops! 发生了一个错误",
                "error_code": "server_error",
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


    @app.exception_handler(SQLAlchemyError)
    async def database__error(request, exc):
        print(str(exc))
        return JSONResponse(
            content={
                "message": "Oops! 发生了一个错误",
                "error_code": "server_error",
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )