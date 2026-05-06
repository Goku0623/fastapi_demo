from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging


# 关闭 Uvicorn 默认的访问日志
logger = logging.getLogger("uvicorn.access")
logger.disabled = True


def register_middleware(app: FastAPI):
    @app.middleware("http")
    async def custom_logging(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        processing_time = time.time() - start_time
        msg = f"{request.client.host}:{request.client.port}{request.url.path} —— {request.method} —— 状态码：{response.status_code} —— 运行了{processing_time}s"
        try:
            print(msg)
        except UnicodeEncodeError:
            print(msg.encode("ascii", errors="replace").decode("ascii"))
        return response

    @app.middleware("http")
    async def authorization(request: Request, call_next):
        # 设置白名单
        white_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/sign_up",
            "/api/v1/auth/pwd-reset-request",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]

        white_paths_prefix = [
            "/api/v1/auth/verify",
            "/api/v1/auth/pwd-reset-confirm",
        ]
    
        if request.url.path in white_paths or any(request.url.path.startswith(prefix) for prefix in white_paths_prefix):
            response = await call_next(request)
            return response
        
        # 非白名单才检查 Authorization
        if not "Authorization" in request.headers:
            # 404
            response = await call_next(request)
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                return response
            
            return JSONResponse(
                content={
                    "msg": "缺少登录凭证",
                    "resolutions": "请前往登录页面登录"
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        response = await call_next(request)
        return response
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True    
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],
    )