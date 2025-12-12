from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Optional
from jose import jwt, JWTError
from config.settings import settings


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        if path in ["/login", "/docs", "openapi.json" ] or method == "OPTIONS":
            response = await call_next(request)
            return response

        token : Optiona[str] = None

        if path == "/api/v1/dashboard":
            raw_token = request.query_params.get("token")
            if raw_token and raw_token.startswith("Bearer "):
                token = raw_token[len("Bearer "):]
            else: 
                return JSONResponse({"detail": "Missing or invalid token"}, status_code=401)

        else:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer"):
                token = auth_header[len("Bearer "):]
            else:
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            request.state.user = payload
        except JWTError:
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        response = await call_next(request)
        return response