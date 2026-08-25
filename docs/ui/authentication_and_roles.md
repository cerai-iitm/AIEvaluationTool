# Authentication And Roles

TDMS and dashboard use a centralized auth service with JWT-based session handling.

## Login Flow
- TDMS login route redirects users to `AUTH_SERVICE_URL/web/login`.
- Dashboard login route also redirects to the same auth service.
- On successful login, auth returns `access_token`, `refresh_token`, `user_name`, and `role`.
- Frontends store tokens in local storage and attach the bearer token to API calls.

![Dashboard after successful login](../../screenshots/loginPage.png)

## Redirect Behavior

Auth service role-based default routing:

- `admin`, `manager` -> Test Case Execution Dashboard (`http://localhost:3000` by default)
- `curator`, `viewer` -> TDMS (`http://localhost:8080/dashboard` by default)

When using NGINX-hosted UIs, set these on auth-service startup:

- `TCE_APP_URL` (dashboard UI URL)
- `TDMS_APP_URL` (TDMS UI URL)

## Default Users

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Manager | `manager` | `manager123` |
| Curator | `curator` | `curator123` |
| Viewer | `viewer` | `viewer123` |

## Permission Model In TDMS UI

The frontend permission utility defines the following role behaviors:

- `admin`: full user management and table management
- `manager`: table management operations
- `curator`: table create/update and record create/update
- `viewer`: restricted read-oriented access in current UI flows

Notes:

- The utility includes backward compatibility checks for a legacy `user` role, which is treated identically to `viewer` (e.g. `canViewActivity` maps `user` -> `viewer`).
- History visibility is explicitly disabled for `viewer` in the current permission helpers.

## Cross-App Navigation Controls

- TDMS sidebar shows Dashboard link (`Home`) for `admin` and `manager`.
- Dashboard sidebar shows TDMS `Test Data` link for all authenticated users.
- Dashboard `User's List` link is limited to `admin`.

## Logout Behavior

Both applications clear local session tokens and redirect to auth login. Auth service also supports `/web/logout` for cookie cleanup.
