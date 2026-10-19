# Docker Run UI

This page explains how to start the application in Docker, which address and port to open, how to change the port, and how a user moves between the screens.

Two modes exist:

- **Production-style stack** (default): one public port, `8100`, for everything. Use this to run and use the tool.
- **Development stack**: hot-reload frontends on separate ports. Use this only when changing frontend or backend code. See [Development Stack](#development-stack).

## Start The Application

From the repository root, after preparing `.env` and the config files in [Setup And Configuration](./setup_and_configuration.md):

```bash
docker compose up -d
```

This starts every service: the database, Redis, the Selenium grid with its browser nodes, the backends, the frontends and `nginx`. The first build usually takes about 10 minutes, depending on network speed and image compilation time.

Check that everything is up:

```bash
docker compose ps
```

All services should be `running`, and the ones with health checks `healthy`.

## Application Addresses

With the default port `8100`:

| Page | Address | Notes |
|---|---|---|
| Test Case Execution (TCE) UI | [http://localhost:8100/](http://localhost:8100/) | start here; log in first |
| TDMS (test data) UI | [http://localhost:8100/tdms/](http://localhost:8100/tdms/) | reached from the sidebar in normal use |
| Health check | [http://localhost:8100/healthz](http://localhost:8100/healthz) | shows `ok` when nginx is up |
| Selenium grid status | [http://localhost:8100/selenium/status](http://localhost:8100/selenium/status) | JSON, for debugging only |

Using another port or another machine? Replace `localhost:8100` in these links with your own host and port. If you changed the port, see [Changing The Port](#changing-the-port).

The **live view of a running test** is not opened by typing an address. Use the **View Test Execution** link on the test run page; it opens the correct browser in a new tab.

First login uses a default account, for example `admin` / `admin123`. Change these after the first login. See [Authentication And Roles](../ui/authentication_and_roles.md) for all default users and what each role can do.

## Ports

### Published Ports

| Port | Default | Changeable | How To Change |
|---|---|---|---|
| Application (nginx) | `8100` | yes | `NGINX_PORT` in `.env`, then `docker compose up -d` |
| Selenium live view (`7900` to `7924`) | published | not normally needed | direct access to each browser node; the UI reaches them through nginx |

### Internal Ports

These are not reachable from outside Docker and need no firewall rule. nginx routes to them:

| Service | Port | Accessed Through |
|---|---|---|
| `app-backend` | 7000 | `/api/` |
| `tdms-backend` | 7250 | `/tdms-api/` |
| `auth-service` | 7500 | `/auth/` |
| `interface-manager` | 8000 | called by `app-backend` |
| `selenium-hub` | 4444 | `/selenium/` |
| `db` | 3306 | internal |
| `redis` | 6379 | internal |

## Changing The Port

Port `8100` may already be in use. Docker then fails to start `nginx` with an error like `port is already allocated` or `address already in use`.

1. Find what is using it:

   ```bash
   # Linux
   ss -ltnp | grep :8100
   # macOS
   lsof -i :8100
   # Windows (PowerShell)
   netstat -ano | findstr :8100
   ```

2. Pick a free port (use one above 1024, for example `8200`) and set it in `.env`:

   ```env
   NGINX_PORT=8200
   ```

3. Apply it. Only `nginx` is recreated, and no rebuild is needed:

   ```bash
   docker compose up -d
   ```

4. Open [http://localhost:8200/](http://localhost:8200/) (your port in place of `8200`).

Nothing else needs to change: the frontends and the login redirects use relative paths, so they follow whatever port the page was opened on.

For a quick one-off without editing `.env`:

```bash
NGINX_PORT=8200 docker compose up -d
```

To serve on the standard web port, set `NGINX_PORT=80` (the port must be free).

## Login And Navigation Flow

```text
Browser ──> nginx ──> TCE frontend (/)  ──┐
                 └──> TDMS frontend (/tdms/) ──┤
                                               ├──> auth-service (/auth/): login, token
                 backends via /api/, /tdms-api/ ┘
```

1. A user opens [http://localhost:8100/](http://localhost:8100/) and is sent to the login page served by `auth-service`.
2. After login the user lands on a screen based on their role:
   - `admin` and `manager` go to the TCE UI (`/`).
   - `curator` and `viewer` go to TDMS (`/tdms/dashboard`).
3. The token is passed back to the app in the address (the part after `#`) and stored by the app.
4. **Test Data** and **User's List** in the TCE sidebar open TDMS. **Home** in the TDMS sidebar returns to TCE. These links go through the login service again so the session carries over, and they open **in the same tab**.
5. The Selenium **View Test Execution** link opens the live browser **in a new tab**, so the running test page stays open.

The two landing addresses are set by `TCE_APP_URL` and `TDMS_APP_URL`, described in [Setup And Configuration](./setup_and_configuration.md).

## Development Stack

Use this when editing frontend or backend code. It runs the hot-reload dev servers and publishes the backend ports on your machine.

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

`docker-compose.dev.yml` is an override: always pass it **after** `docker-compose.yml` as shown. To avoid retyping, set it once for your shell:

```bash
export COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml
docker compose up -d --build
```

On Windows, separate the files with `;` instead of `:`.

In development there is no single entrypoint; each part has its own port:

| Component | Address |
|---|---|
| TCE frontend (hot reload) | [http://localhost:3000/](http://localhost:3000/) |
| TDMS frontend (hot reload) | [http://localhost:8080/](http://localhost:8080/) |
| `app-backend` API docs | [http://localhost:7000/docs](http://localhost:7000/docs) |
| `tdms-backend` | [http://localhost:7250/](http://localhost:7250/) |
| `auth-service` API docs | [http://localhost:7500/docs](http://localhost:7500/docs) |
| `interface-manager` API docs | [http://localhost:8000/docs](http://localhost:8000/docs) |
| MariaDB | `localhost:3306` |

Differences from the production-style stack:

- The frontends call the backends with absolute `localhost` addresses, and the login redirects point to `3000` and `8080`.
- The repository is mounted into the backend containers. Restart a backend container to pick up Python changes: `docker compose restart app-backend`.
- Frontend source changes reload in the browser by themselves.
- Port clash on `3000`, `8080`, `7000`, `7250`, `7500`, `8000` or `3306`? Change the left-hand number of that port in `docker-compose.dev.yml`. If you change `3000`, `7000`, `7250`, `7500` or `8080`, also update the matching `localhost` addresses in the same file.
- `nginx` still starts, on port `8100`, but it is not the entrypoint. The only reason to use it in development is the live view: the **View Test Execution** link is a path that only nginx serves. If the link does not show the browser from the dev frontend, copy its path (`/vnc-proxy/...`) and open it on `http://localhost:8100` instead.

Stop and reset work the same as below; pass the same `-f` files, or keep `COMPOSE_FILE` set.

## Detailed User Manuals

- [UI Overview](../ui/index.md)
- [Authentication And Roles](../ui/authentication_and_roles.md)
- [TDMS Dashboard Manual](../ui/tdms_dashboard_manual.md)
- [Test Runs Manual](../ui/test_runs_manual.md)
- [Run Configuration Manual](../ui/run_configuration_manual.md)
- [Analysis And Run Details Manual](../ui/analysis_and_run_details_manual.md)
- [API Reference](../ui/api_reference.md)
- [Troubleshooting](../ui/troubleshooting.md)

## Stop The Stack

Stops and removes containers; data is kept:

```bash
docker compose down
```

## Reset The Stack (Delete Data)

Also deletes the volumes (database, downloaded models, logs). This cannot be undone:

```bash
docker compose down -v
```

## Restarting The Stack

`--build` is not required to start the application. It is only needed when the code has changed. If you have already built the images and nothing changed, start with:

```bash
docker compose up -d
```

This reuses the existing images, so it starts faster. Add `--build` again after you pull new code, edit the source, or change a frontend build setting (`REACT_APP_*` or `VITE_*`). Without it, Docker keeps running the old images and your changes will not appear.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `port is already allocated` on start | [Changing The Port](#changing-the-port) |
| Page does not load, `docker compose ps` shows `starting` | Wait for health checks; check with `docker compose logs -f nginx app-backend` |
| `502 Bad Gateway` right after an update | nginx kept the old container address: `docker compose restart nginx` |
| Login loops back to the login page | Open the app on one address only (not a mix of `localhost` and an IP); clear site data and retry |
| Live view link shows nothing | The test is not running yet, or has finished; the browser exists only during a run |
