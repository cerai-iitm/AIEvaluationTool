from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from jose import jwt, JWTError
import os

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "@cerai")
ALGORITHM = "HS256"

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exclude_paths=None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/docs", "/openapi.json", "/redoc", "/health"]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Skip auth for certain paths
        if path in self.exclude_paths or method == "OPTIONS":
            response = await call_next(request)
            return response

        # Check for token in Authorization header or cookie
        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header and auth_header.startswith("Bearer"):
            token = auth_header[len("Bearer "):]

        if not token:
            # Support HTTP-only cookie auth
            token = request.cookies.get("access_token") or request.cookies.get("accessToken")

        if not token:
            return JSONResponse({"detail": "Authorization header missing"}, status_code=401)

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "access":
                return JSONResponse({"detail": "Invalid token type"}, status_code=401)
            request.state.user = payload
        except JWTError:
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        response = await call_next(request)
        return response
