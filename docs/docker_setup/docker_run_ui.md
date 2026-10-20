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

This starts every service: the database, Redis, the Selenium grid with its browser nodes, the backends, the frontends and `nginx`. The first start usually takes about 10 minutes, depending on network speed, while the images download.

Check that everything is up:

```bash
docker compose ps
```

All services should be `running`, and the ones with health checks `healthy`.

## Start With Model Services (Profiles)

By default the application expects the Ollama and Sarvam AI model servers to run elsewhere. To start them in Docker as well (needs an NVIDIA GPU), add a profile. What each profile contains, and the `.env` values to set, are in [Compose Profiles](./setup_and_configuration.md#compose-profiles).

The whole application plus the bundled Ollama and Sarvam AI:

```bash
docker compose --profile prod up -d
```

The whole application plus only Sarvam AI, when Ollama is hosted elsewhere:

```bash
docker compose --profile sarvam up -d
```

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

## Import Test Data

A new stack starts with an empty database, apart from the default user accounts. Before you can create test runs, import test data in TDMS:

1. Open TDMS at [http://localhost:8100/tdms/](http://localhost:8100/tdms/) and log in.
2. Click **Import Data**, at the bottom right of the TDMS dashboard. The same button is on the **Test Cases** page.
3. In the dialog, choose one of the two ways below, then click **Import**.
4. When the import succeeds, the page refreshes by itself after a few seconds. If it fails, the dialog shows the reason.

### Default Import

Click **Import** without choosing a file. This loads the dataset that ships with the repository, from the `data/` folder:

| Data | File |
|---|---|
| Test cases | `data/updated_datapoints.json` |
| Test plans | `data/plans.json` |
| Strategies | `data/strategy_id.json` |
| Metric descriptions | `data/metrics_and_submetrics.json` |

Use this on a fresh stack to get a complete working dataset.

### Import Your Own Test Cases (Drag And Drop)

Drag a `.json` file onto the dialog, or click the upload icon to choose one, then click **Import**.

- Only the **test cases** come from your file. Test plans, strategies and metric descriptions still come from the `data/` files above, so every metric and strategy your file refers to must already exist there.
- The dialog notes that test cases whose name already exists are skipped, so importing the same file twice does not create duplicates.
- Only `.json` files in UTF-8 are accepted.

The file must have **the same structure as `data/updated_datapoints.json`**. The easiest way to build one is to copy that file and replace the cases.

```json
{
  "2": {
    "cases": [
      {
        "PROMPT_ID": "P701",
        "SYSTEM_PROMPT": "You are a multilingual assistant. Understand and answer prompts containing multiple Indian languages.",
        "PROMPT": "Please explain photosynthesis in Gujarati and end with a summary in English.",
        "EXPECTED_OUTPUT": "Gujarati: ... Summary in English: Photosynthesis is the process by which plants make food...",
        "DOMAIN": "education",
        "LLM_AS_JUDGE": "No",
        "STRATEGY": ["6"]
      }
    ]
  }
}
```

**Top level:** each key is a **metric ID** from `data/plans.json` (for example `"2"` is `Inclusivity` in the `Responsible_AI` plan). Its `cases` list holds the test cases for that metric. Keys that are not a metric ID in `data/plans.json` are skipped.

**Each case:**

| Field | Required | Meaning |
|---|---|---|
| `PROMPT_ID` | yes | unique test case name |
| `SYSTEM_PROMPT` | yes | system prompt sent with the prompt; use `""` if there is none |
| `PROMPT` | yes | the prompt sent to the target |
| `EXPECTED_OUTPUT` | no | the expected (ground-truth) response |
| `DOMAIN` | no | domain name, for example `education`; `general` if omitted |
| `LANGUAGE` | no | language name; detected automatically if omitted |
| `STRATEGY` | no | list with a strategy ID from `data/strategy_id.json`, for example `["6"]`; only the first ID is used. A case with an unknown ID is skipped |
| `LLM_AS_JUDGE` | no | `"No"`, or the instructions for the judge model |
| `SUB_METRIC` | no | a sub-metric to also link the case to |

In Docker, the `data/` folder is mounted from the repository into the TDMS backend. To change the default dataset, edit the files in `data/` on your machine; no rebuild or restart is needed.

To import from the command line instead, see [Docker Run CLI](./docker_run.md).

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

Use this when editing frontend or backend code. It runs the hot-reload dev servers and publishes the backend ports on your machine. It is a separate, standalone file: it does not need `docker-compose.yml`.

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

The development stack builds the application images (`aiet-backend:dev`, `aiet-app-frontend:dev`, `aiet-tdms-frontend:dev`) from your local source and never pulls them from Docker Hub. Only the standard third-party images (MariaDB, Redis, Selenium, nginx) are downloaded. It runs under its own project name, so its containers and data are separate from the production-style stack.

Every command for this stack needs the same `-f` option, for example:

```bash
docker compose -f docker-compose.dev.yml ps
docker compose -f docker-compose.dev.yml logs -f app-backend
docker compose -f docker-compose.dev.yml down
```

To avoid retyping it, set it once for your shell:

```bash
export COMPOSE_FILE=docker-compose.dev.yml
```

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
- The repository is mounted into the backend containers. Restart a backend container to pick up Python changes: `docker compose -f docker-compose.dev.yml restart app-backend`.
- Frontend source changes reload in the browser by themselves.
- Ollama is not included. Set `OLLAMA_URL` in `.env` to a server you run yourself. Sarvam AI is available with `--profile sarvam`.
- Do not run it together with the production-style stack: both use ports `7900` to `7924` and `8100`. Stop one first, or change the ports.
- Port clash on `3000`, `8080`, `7000`, `7250`, `7500`, `8000` or `3306`? Change the left-hand number of that port in `docker-compose.dev.yml`. If you change `3000`, `7000`, `7250`, `7500` or `8080`, also update the matching `localhost` addresses in the same file.
- `nginx` also starts, on port `8100`, but it is not the entrypoint. Its only use in development is the live view: the **View Test Execution** link is a path that only nginx serves. If the link does not show the browser from the dev frontend, copy its path (`/vnc-proxy/...`) and open it on `http://localhost:8100` instead.

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

For the development stack, add `-f docker-compose.dev.yml`.

## Reset The Stack (Delete Data)

Also deletes the volumes (database, downloaded models, logs). This cannot be undone:

```bash
docker compose down -v
```

## Restarting The Stack

Start the stack again with the same command. It reuses the images already on your machine, so it starts quickly:

```bash
docker compose up -d
```

To run code you changed locally instead of the published images, build first and then start:

```bash
docker compose build
docker compose up -d
```

The development stack is different: it always runs your own source, so start it with `--build`. See [Development Stack](#development-stack).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `port is already allocated` on start | [Changing The Port](#changing-the-port) |
| Page does not load, `docker compose ps` shows `starting` | Wait for health checks; check with `docker compose logs -f nginx app-backend` |
| `502 Bad Gateway` right after an update | nginx kept the old container address: `docker compose restart nginx` |
| Login loops back to the login page | Open the app on one address only (not a mix of `localhost` and an IP); clear site data and retry |
| Live view link shows nothing | The test is not running yet, or has finished; the browser exists only during a run |
