# Docker Run UI

This page explains how to run and use the UI through Docker in production and development modes.

## Production UI Stack

```bash
docker compose up -d --build nginx
```

Starting `nginx` brings up the dependent UI and backend services needed for the dashboard routes.

## Verify Running Containers

```bash
docker compose ps
```

## Production URLs To Open

- TCE UI: `http://localhost:${NGINX_PORT:-80}/`
- TDMS UI: `http://localhost:${NGINX_PORT:-80}/tdms/`
- Selenium live browser: `http://localhost:${NGINX_PORT:-80}/selenium/`
- Health check: `http://localhost:${NGINX_PORT:-80}/healthz`

## Port Information

- Public application port: `${NGINX_PORT:-80}` mapped to container `80`

Internal service ports:

- `app-backend`: `7000`
- `auth-service`: `7500`
- `tdms-backend`: `7250`
- `interface-manager`: `8000`
- `selenium-browser`: `4444` (WebDriver), `7900` (noVNC)
- `db`: `3306`

Internal ports are handled by nginx routing and usually do not need direct browser access.

## Development UI Stack

Use the development override when you need direct frontend dev servers and exposed backend ports:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Development URLs:

- Nginx entrypoint: `http://localhost:${NGINX_PORT:-80}/`
- TCE frontend dev server: `http://localhost:3000`
- TDMS frontend dev server: `http://localhost:8080`
- Selenium live browser: `http://localhost:7900`
- Dashboard backend API docs: `http://localhost:7000/docs`
- TDMS backend: `http://localhost:7250`
- Auth service docs: `http://localhost:7500/docs`
- Interface Manager docs: `http://localhost:8000/docs`

## UI Usage Flow

1. Open TCE UI at `http://localhost:${NGINX_PORT:-80}/`.
2. Open TDMS UI at `http://localhost:${NGINX_PORT:-80}/tdms/` when managing test data.
3. Open Selenium view at `http://localhost:${NGINX_PORT:-80}/selenium/` for browser-backed runs.
4. Confirm stack health at `http://localhost:${NGINX_PORT:-80}/healthz` before long executions.

## Detailed User Manual References

- [UI Overview](../ui/index.md)
- [Authentication And Roles](../ui/authentication_and_roles.md)
- [TDMS Dashboard Manual](../ui/tdms_dashboard_manual.md)
- [Test Runs Manual](../ui/test_runs_manual.md)
- [Run Configuration Manual](../ui/run_configuration_manual.md)
- [Analysis And Run Details Manual](../ui/analysis_and_run_details_manual.md)
- [API Reference](../ui/api_reference.md)
- [Troubleshooting](../ui/troubleshooting.md)

## Stop UI Stack

Production:

```bash
docker compose down
```

Development:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

## Reset UI Stack (Remove Volumes)

Production:

```bash
docker compose down -v
```

Development:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```
