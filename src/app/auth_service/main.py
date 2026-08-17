from fastapi import FastAPI, Depends, Response, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from controllers import auth
from database.database import get_db, init_db, seed_users
from schemas.auth import LoginRequest, RefreshTokenRequest, LogoutRequest
from contextlib import asynccontextmanager
from urllib.parse import urlencode
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

AUTH_BASE_PATH = os.getenv("AUTH_BASE_PATH", "/auth").strip()
if AUTH_BASE_PATH in {"", "/"}:
    AUTH_BASE_PATH = ""
elif not AUTH_BASE_PATH.startswith("/"):
    AUTH_BASE_PATH = f"/{AUTH_BASE_PATH}"


def with_auth_base(path: str) -> str:
    return f"{AUTH_BASE_PATH}{path}" if AUTH_BASE_PATH else path


DEFAULT_PORTAL_URL = os.getenv("AUTH_DEFAULT_PORTAL_URL", with_auth_base("/web/portal"))
TCE_APP_URL = os.getenv("TCE_APP_URL", "/")
TDMS_APP_URL = os.getenv("TDMS_APP_URL", "/tdms/dashboard")


def resolve_redirect_url(role: str | None, requested_return_url: str | None) -> str:
    if requested_return_url and requested_return_url != DEFAULT_PORTAL_URL:
        return requested_return_url

    normalized_role = (role or "").strip().lower()
    if normalized_role in {"admin", "manager"}:
        return TCE_APP_URL
    if normalized_role in {"curator", "viewer"}:
        return TDMS_APP_URL
    return requested_return_url or TDMS_APP_URL

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Auth Service...")
    init_db()
    seed_users()
    yield
    logging.info("Shutting down Auth Service...")

app = FastAPI(
    title="Auth Service",
    description="Central Authentication Service for AI Evaluation Tool",
    version="1.0.0",
    lifespan=lifespan,
    root_path=AUTH_BASE_PATH or ""
)

tdms_assets_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "TDMS", "front-end", "src", "assets")
)
if os.path.isdir(tdms_assets_dir):
    app.mount("/web-assets", StaticFiles(directory=tdms_assets_dir), name="web-assets")
    if AUTH_BASE_PATH:
        app.mount(
            f"{AUTH_BASE_PATH}/web-assets",
            StaticFiles(directory=tdms_assets_dir),
            name="web-assets-prefixed",
        )

raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
cors_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
allow_origin_regex = None
if not cors_origins:
    cors_origins = ["*"]
    # Allow any localhost/127.0.0.1 port in dev (covers Vite/CRA port changes)
    # allow_origin_regex = r"^https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/login")
async def login(
    user: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate user and return JWT tokens."""
    token_response = auth.login(db, user)
    cookie_secure = os.getenv("COOKIE_SECURE", "").lower() in {"1", "true", "yes"}
    cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax")
    response.set_cookie(
        "access_token",
        token_response.access_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
    )
    response.set_cookie(
        "refresh_token",
        token_response.refresh_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
    )
    return token_response

@app.post("/refresh")
async def refresh_token(token_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    return auth.refresh_access_token(db, token_data)

@app.post("/logout")
async def logout(token_data: LogoutRequest, response: Response):
    """Logout user by revoking refresh token."""
    result = auth.logout(token_data)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return result

@app.get("/web/login", response_class=HTMLResponse)
async def web_login(
    request: Request,
    return_url: str = DEFAULT_PORTAL_URL,
    db: Session = Depends(get_db),
):
    refresh_token_cookie = request.cookies.get("refresh_token")
    if refresh_token_cookie:
        try:
            tokens = auth.refresh_access_token(db, RefreshTokenRequest(refresh_token=refresh_token_cookie))
            redirect_target = resolve_redirect_url(tokens.role, return_url)
            redirect_params = {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "user_name": tokens.user_name,
                "role": tokens.role,
            }
            redirect_url = f"{redirect_target}#{urlencode(redirect_params)}"
            response = RedirectResponse(redirect_url)
            cookie_secure = os.getenv("COOKIE_SECURE", "").lower() in {"1", "true", "yes"}
            cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax")
            response.set_cookie("access_token", tokens.access_token, httponly=True, secure=cookie_secure, samesite=cookie_samesite, path="/")
            response.set_cookie("refresh_token", tokens.refresh_token, httponly=True, secure=cookie_secure, samesite=cookie_samesite, path="/")
            return response
        except Exception:
            pass

    cerai_logo_url = with_auth_base("/web-assets/cerai-logo.png")
    iit_logo_url = with_auth_base("/web-assets/iit-logo.png")
    background_url = with_auth_base("/web-assets/iit-background.jpeg")
    AIEvaluLogo_url = with_auth_base("/web-assets/logo.png")

    html = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
      <meta charset='UTF-8' />
      <link rel="icon" type="image/png" href="{AIEvaluLogo_url}" />
      <link rel="apple-touch-icon" type="image/png" href="{AIEvaluLogo_url}" />
      
      <meta name='viewport' content='width=device-width, initial-scale=1.0' />
      <title>AI Evaluation Tool</title>
      <style>
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          min-height: 100vh;
          font-family: Arial, sans-serif;
          color: #1f2937;
          background:
            linear-gradient(rgba(0, 0, 0, 0.42), rgba(0, 0, 0, 0.42)),
            url('{background_url}') center center / cover no-repeat fixed;
        }}
        .page {{
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }}
        .topbar {{
          height: 84px;
          background: rgba(255, 255, 255, 0.96);
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 32px;
          box-shadow: 0 2px 12px rgba(15, 23, 42, 0.08);
        }}
        .brand-logo {{
          height: 52px;
          width: auto;
          object-fit: contain;
        }}
        .iit-logo {{
          height: 58px;
          width: 58px;
          object-fit: contain;
        }}
        .hero {{
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: flex-end;
          padding: 40px 10vw 40px 5vw;
        }}
        .card {{
          width: min(100%, 520px);
          padding: 40px 40px 32px;
          border-radius: 16px;
          background: rgba(255, 255, 255, 0.76);
          backdrop-filter: blur(8px);
          box-shadow: 0 24px 60px rgba(15, 23, 42, 0.22);
        }}
        .title {{
          margin: 0 0 28px;
          text-align: center;
          font-size: 2.05rem;
          font-weight: 700;
          line-height: 1.15;
          color: #1f2937;
        }}
        .field {{
          margin-bottom: 22px;
        }}
        .label {{
          display: block;
          margin-bottom: 10px;
          font-size: 1.05rem;
          font-weight: 600;
          color: #2b2f36;
        }}
        input {{
          width: 100%;
          height: 48px;
          padding: 0 44px 0 14px;
          border: 1px solid rgba(148, 163, 184, 0.55);
          border-radius: 4px;
          background: rgba(255, 255, 255, 0.95);
          font-size: 1rem;
          outline: none;
        }}
        input:focus {{
          border-color: #22c55e;
          box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.18);
        }}
        .password-wrap {{
          position: relative;
        }}
        .toggle-password {{
          position: absolute;
          top: 50%;
          right: 12px;
          transform: translateY(-50%);
          border: 0;
          padding: 4px;
          margin: 0;
          width: 32px;
          height: 32px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          color: #6b7280;
          cursor: pointer;
        }}
        .toggle-password:hover {{
          color: #374151;
        }}
        .toggle-password svg {{
          width: 20px;
          height: 20px;
          stroke: currentColor;
        }}
        .login-btn {{
          display: block;
          width: 144px;
          height: 48px;
          margin: 18px auto 0;
          border: none;
          border-radius: 4px;
          background: #2dbd2d;
          color: #fff;
          font-size: 1.05rem;
          font-weight: 700;
          cursor: pointer;
          transition: background 0.2s ease;
        }}
        .login-btn:hover {{
          background: #25a525;
        }}
        .error {{
          min-height: 22px;
          margin-top: 16px;
          text-align: center;
          color: #b42318;
          font-size: 0.95rem;
          font-weight: 600;
        }}
        @media (max-width: 900px) {{
          .hero {{
            justify-content: center;
            padding: 32px 20px;
          }}
          .card {{
            padding: 28px 22px 24px;
          }}
          .title {{
            font-size: 1.7rem;
          }}
          .topbar {{
            padding: 0 18px;
          }}
          .brand-logo {{
            height: 42px;
          }}
          .iit-logo {{
            height: 46px;
            width: 46px;
          }}
        }}
      </style>
    </head>
    <body>
    <div class='page'>
      <header class='topbar'>
        <img class='brand-logo' src='{cerai_logo_url}' alt='CeRAI logo' />
        <img class='iit-logo' src='{iit_logo_url}' alt='IIT Madras logo' />
      </header>
      <main class='hero'>
        <section class='card'>
          <h1 class='title'>AI Evaluation Tool <br> Login</h1>
          <form id='login-form'>
            <div class='field'>
              <label class='label' for='user_name'>User Name :</label>
              <input id='user_name' name='user_name' autocomplete='username' required />
            </div>
            <div class='field'>
              <label class='label' for='password'>Password :</label>
              <div class='password-wrap'>
                <input id='password' name='password' type='password' autocomplete='current-password' required />
                <button class='toggle-password' id='toggle-password' type='button' aria-label='Show password'>
                  <svg class='eye-icon' viewBox='0 0 24 24' fill='none' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>
                    <path d='M9.88 9.88a3 3 0 1 0 4.24 4.24'></path>
                    <path d='M10.73 5.08A10.43 10.43 0 0 1 12 5c6.5 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68'></path>
                    <path d='M6.61 6.61A13.53 13.53 0 0 0 2 12s3.5 7 10 7a9.74 9.74 0 0 0 5.39-1.61'></path>
                    <path d='M2 2l20 20'></path>
                  </svg>
                </button>
              </div>
            </div>
            <button class='login-btn' type='submit'>Login</button>
          </form>
          <div id='error' class='error'></div>
        </section>
      </main>
    </div>
    <script>
      const q = new URLSearchParams(window.location.search);
      const returnUrl = q.get('return_url') || {return_url!r};
      const defaultPortalUrl = {DEFAULT_PORTAL_URL!r};
      const authBasePath = {AUTH_BASE_PATH!r};
      const tceAppUrl = {TCE_APP_URL!r};
      const tdmsAppUrl = {TDMS_APP_URL!r};
      const resolveRedirectUrl = (role, requestedReturnUrl) => {{
        if (requestedReturnUrl && requestedReturnUrl !== defaultPortalUrl) {{
          return requestedReturnUrl;
        }}
        const normalizedRole = (role || '').trim().toLowerCase();
        if (normalizedRole === 'admin' || normalizedRole === 'manager') {{
          return tceAppUrl;
        }}
        if (normalizedRole === 'curator' || normalizedRole === 'viewer') {{
          return tdmsAppUrl;
        }}
        return requestedReturnUrl || tdmsAppUrl;
      }};
      const passwordInput = document.getElementById('password');
      const togglePassword = document.getElementById('toggle-password');
      const eyeIcon = `
        <svg class='eye-icon' viewBox='0 0 24 24' fill='none' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>
          <path d='M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z'></path>
          <circle cx='12' cy='12' r='3'></circle>
        </svg>
      `;
      const eyeOffIcon = `
        <svg class='eye-icon' viewBox='0 0 24 24' fill='none' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>
          <path d='M9.88 9.88a3 3 0 1 0 4.24 4.24'></path>
          <path d='M10.73 5.08A10.43 10.43 0 0 1 12 5c6.5 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68'></path>
          <path d='M6.61 6.61A13.53 13.53 0 0 0 2 12s3.5 7 10 7a9.74 9.74 0 0 0 5.39-1.61'></path>
          <path d='M2 2l20 20'></path>
        </svg>
      `;
      togglePassword.onclick = () => {{
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
        togglePassword.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
        togglePassword.innerHTML = isPassword ? eyeIcon : eyeOffIcon;
      }};
      document.getElementById('login-form').onsubmit = async (e) => {{
        e.preventDefault();
        const user_name = document.getElementById('user_name').value;
        const password = document.getElementById('password').value;
        const res = await fetch(`${{authBasePath}}/login`, {{
          method:'POST',
          headers:{{'Content-Type':'application/json'}},
          body: JSON.stringify({{ user_name, password }})
        }});
        const data = await res.json();
        if (!res.ok) {{
          document.getElementById('error').innerText = data.detail || 'Login failed';
          return;
        }}
        const redirectUrl = resolveRedirectUrl(data.role, returnUrl);
        const url = new URL(redirectUrl, window.location.origin);
        const fragment = new URLSearchParams({{
          access_token: data.access_token,
          refresh_token: data.refresh_token,
          user_name: data.user_name,
          role: data.role,
        }}).toString();
        window.location.href = `${{url.toString()}}#${{fragment}}`;
      }};
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/web/portal", response_class=HTMLResponse)
async def web_portal():
    tdms_url = TDMS_APP_URL
    tce_url = TCE_APP_URL
    html = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
      <meta charset='UTF-8' />
      <meta name='viewport' content='width=device-width, initial-scale=1.0' />
      <title>Choose Application</title>
      <style>
        body {{ font-family: Arial, sans-serif; background:#f5f7ff; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; }}
        .card {{ background:white; border-radius:12px; box-shadow:0 10px 25px rgba(0,0,0,0.08); width:min(95%,520px); padding:24px; }}
        .btn {{ display:block; width:100%; padding:12px; margin:10px 0; border:none; border-radius:8px; background:#1f2937; color:white; font-size:1rem; text-align:center; text-decoration:none; }}
        .muted {{ color:#6b7280; font-size:.9rem; }}
      </style>
    </head>
    <body>
    <div class='card'>
      <h2>Continue to an application</h2>
      <p class='muted'>Select where you want to go. Your login tokens will be passed automatically.</p>
      <a id='tdms-link' class='btn' href='{tdms_url}'>TDMS</a>
      <a id='tce-link' class='btn' href='{tce_url}'>TestCaseExecutorDashboard</a>
      <p id='status' class='muted'></p>
    </div>
    <script>
      const hash = window.location.hash.replace(/^#/, '');
      const values = Object.fromEntries(new URLSearchParams(hash));
      const hasTokens = values.access_token && values.refresh_token;
      const tdmsBase = '{tdms_url}';
      const tceBase = '{tce_url}';
      if (hasTokens) {{
        const fragment = new URLSearchParams(values).toString();
        document.getElementById('tdms-link').href = `${{tdmsBase}}#${{fragment}}`;
        document.getElementById('tce-link').href = `${{tceBase}}#${{fragment}}`;
      }} else {{
        document.getElementById('status').innerText = 'No login tokens found. Please sign in again.';
      }}
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
@app.get("/web/logout")
async def web_logout(
    request: Request,
    return_url: str = "/",
    db: Session = Depends(get_db),
):
    refresh_token_cookie = request.cookies.get("refresh_token")
    if refresh_token_cookie:
        try:
            auth.logout(LogoutRequest(refresh_token=refresh_token_cookie))
        except Exception:
            pass
    response = RedirectResponse(url=return_url)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return response


def add_prefixed_route_alias(path: str, endpoint, *, methods: list[str], **kwargs) -> None:
    if not AUTH_BASE_PATH:
        return

    app.add_api_route(
        f"{AUTH_BASE_PATH}{path}",
        endpoint,
        methods=methods,
        include_in_schema=False,
        **kwargs,
    )


add_prefixed_route_alias("/login", login, methods=["POST"])
add_prefixed_route_alias("/refresh", refresh_token, methods=["POST"])
add_prefixed_route_alias("/logout", logout, methods=["POST"])
add_prefixed_route_alias("/web/login", web_login, methods=["GET"], response_class=HTMLResponse)
add_prefixed_route_alias("/web/portal", web_portal, methods=["GET"], response_class=HTMLResponse)
add_prefixed_route_alias("/web/logout", web_logout, methods=["GET"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=7500, reload=True)
