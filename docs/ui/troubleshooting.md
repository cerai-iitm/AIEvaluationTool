# Troubleshooting

Use this guide when TDMS and dashboard are running but not behaving as expected.

## Auth Redirect Loop

Symptoms:

- repeated redirect between app and login
- immediate return to login after sign-in

Checks:

- verify auth service is up on `http://localhost:7500`
- verify app auth URLs (`VITE_AUTH_SERVICE_URL`, `REACT_APP_AUTH_SERVICE_URL`)
- clear local storage tokens and sign in again

## Dashboard Frontend Fails On Startup Or Shows Blank Screen

Symptoms:

- dashboard fails early with API URL related runtime errors
- blank page after `npm start`

Checks:

- ensure `REACT_APP_API_BASE_URL` is set (mandatory in dashboard frontend config)
- verify value points to the dashboard backend (example: `http://localhost:7000`)
- if TDMS links or current-user calls fail, also set `REACT_APP_TDMS_API_BASE_URL=http://localhost:7250`

## NGINX Serves Old UI Content

Symptoms:

- UI changes not visible after deployment

Checks:

- rebuild the UI (`npm run build`)
- re-copy build artifacts to NGINX root directories
- clear browser cache and hard refresh
- verify NGINX root path points to correct folder

## NGINX Route 404 On Page Refresh

Symptoms:

- direct refresh of routes like `/dashboard` or `/test-runs/...` returns `404`

Checks:

- verify NGINX `location /` uses `try_files $uri $uri/ /index.html;`
- run `sudo nginx -t` and reload NGINX after config edits

## Cross-UI Navigation Opens Wrong URL

Symptoms:

- TDMS `Home` opens wrong dashboard URL
- Dashboard `Test Data` link points to wrong TDMS URL

Checks:

- TDMS build env: `VITE_TEST_RUNS_HOME_URL`
- Dashboard build env: `REACT_APP_TEST_DATA_URL`
- rebuild both UIs after changing these environment values

## TDMS Loads But Data APIs Fail

Symptoms:

- dashboard cards show errors or zero values unexpectedly
- CRUD tables fail to load

Checks:

- confirm TDMS backend is running on `http://localhost:7250`
- confirm bearer token is included in API calls
- verify database config in root `config.json`

## Dashboard Filters Or Start-Run Options Are Empty

Symptoms:

- target/plan filters not populated
- metric list not loading after plan selection

Checks:

- verify `GET /get_all_filters` returns data
- confirm seeded test data exists in database
- ensure TDMS-managed entities are available (targets, plans, metrics)

## Run Starts But No Live Progress

Symptoms:

- run starts but progress loop does not update

Checks:

- ensure dashboard backend WebSocket endpoint is reachable: `/ws/test-run`
- verify frontend `REACT_APP_API_BASE_URL` points to dashboard backend
- check backend logs for WebSocket disconnects

## Continue Run Fails

Symptoms:

- `continue-run` returns not found or validation errors

Checks:

- confirm run name is valid and already exists
- verify run was created in the same connected database
- confirm run detail records exist for the selected run

## Report Download Fails

Symptoms:

- report action completes without file download

Checks:

- verify `/report/{run_name}` responds successfully
- check write permissions for the repository `reports/` directory
- confirm run has analysis outputs before report generation

## SQLite Locking Or Concurrency Issues

Symptoms:

- intermittent write failures during heavy activity

Checks:

- avoid running multiple conflicting write-heavy operations in parallel
- switch to MariaDB for multi-user or high-throughput usage

## Recommended Operational Practices

- keep `config.json` under version control for team-consistent ports
- align `db.engine` and `db.engine_type` values
- start auth and backends before frontends
- verify interface manager before long run executions
