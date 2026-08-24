# Architecture And Components

TDMS and the Test Case Execution Dashboard share authentication, core data models, and database state, while serving different operational needs.

## Runtime Architecture

### Docker Deployment (with Nginx)

NGINX reverse proxy serves all services behind a single port (80, or 443 for HTTPS) with unified URL paths.

```Architecture
┌─────────────────────────────────────────────────────────────────────────┐
│                          NGINX Reverse Proxy (Port 80/443)              │
├─────────────┬──────────────────────┬────────────────┬───────────────────┤
│             │                      │                │                   │
▼             ▼                      ▼                ▼                   ▼
/             /tdms/              /auth/          /tdms-api/            /api/
│             │                     │                │                    │
▼             ▼                     ▼                ▼                    ▼

┌──────────┐  ┌──────────────────┐  ┌──────────────┐  ┌─────────────────────┐
│ TCE      │  │   TDMS Frontend  │  │ Auth Service │  │  TDMS Backend       │
│ Dashboard│  │ (Vite/React)     │  │  (FastAPI)   │  │  (FastAPI)          │
│ Frontend │  │ TypeScript       │  │              │  │  Internal Port      │
│ (CRA)    │  │ Radix UI         │  │ JWT Token    │  │                     │
│          │  │ Tailwind CSS     │  │ Authority    │  │ v1 & v2 REST APIs   │
└────┬─────┘  └────────┬─────────┘  └──────┬───────┘  └──────────┬──────────┘
     │                 │ JWT Token         │                     │
     │                 └───────────────────┼─────────────────────┘
     │                                     │
     │ JWT Token / role-based config       │
     └─────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│ TCE Dashboard Backend (FastAPI)                                            │
│ • Test run orchestration & execution                                       │
│ • Filtering, analysis, and reporting APIs                                  │
│ • WebSocket endpoint: /ws/test-run (real-time updates)                     │
└─────────┬─────────────────────────────────────────────────────────┬────────┘
          │                                                         │
          │ Browser Automation                    Shared            │
          │ Control via REST Client                Database         │
          │                                        (MariaDB)        │
          ▼                                                         ▼
┌──────────────────────────────────┐                    ┌──────────────────┐
│ Interface Manager (FastAPI)      │ ◄──────────────────│   Database       │
│                                  │                    │ (Centralized)    │
│ • Browser automation (Selenium)  │ ──────────────────►│                  │
│ • WhatsApp Web interaction       │    Read/Write      │ Test Data:       │
│ • LLM API integration            │                    │ • Test Cases     │
│   (OpenAI, Gemini, Sarvam AI)    │                    │ • Test Plans     │
│ • Conversation management        │                    │ • Strategies     │
└──────────────────────────────────┘                    │ • Metrics        │
                                                        │ • Prompts        │
                                                        │ • Test Runs      │
                                                        │ • Results        │
                                                        └──────────────────┘
```

**Deployment Details (Docker):**
- Services run in Docker containers with internal networking
- NGINX container handles all routing and SSL/TLS
- Frontends are served as static assets by NGINX
- Backends communicate over internal Docker network
- Only ports 80/443 exposed externally

---

### Local Development (5 Separate Ports)

Each service runs independently with direct port access, no reverse proxy.

```Architecture 
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ TCE Dashboard    │     │ TDMS Frontend    │     │ Auth Service     │
│ Frontend (CRA)   │     │ (Vite/React)     │     │ (FastAPI)        │
│ http://localhost │     │ http://localhost │     │ http://localhost │
│ :3000            │     │ :8080            │     │ :7500            │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │ JWT Token
             ┌────────────────────┴────────────────────┐
             │                                         │
             ▼                                         ▼
   ┌──────────────────────┐       ┌──────────────────────────┐
   │ TCE Backend (Port    │       │ TDMS Backend (Port 7250) │
   │ 7000)                │       │ FastAPI                  │
   │ FastAPI              │       │                          │
   │ • Run orchestration  │       │ REST APIs for test data  │
   │ • Analysis APIs      │       │ v1 & v2 endpoints        │
   │ • WebSocket /ws/...  │       │ JWT validation           │
   └────────┬─────────────┘       └────────┬─────────────────┘
            │                              │
            │ REST Client              JWT validated
            │ Control                  requests
            ▼                              │
   ┌──────────────────────┐                │
   │ Interface Manager    │◄───────────────┘
   │ (Port 8000)          │
   │ FastAPI + Selenium   │
   │                      │
   │ • Browser automation │
   │ • LLM integration    │
   └─────────┬────────────┘
             │
             │ Read/Write
             ▼
   ┌──────────────────────┐
   │ Shared Database      │
   │ (MariaDB/SQLite)     │
   │                      │
   │ All services access  │
   │ via SQLAlchemy ORM   │
   └──────────────────────┘
```

**Development Details (5 Ports):**
- Each backend runs on its own port (7000, 7250, 7500, 8000)
- TCE Dashboard Frontend on port 3000 (CRA default)
- TDMS Frontend on port 8080 (configured in `vite.config.ts`, not the Vite default)
- Frontends make direct API calls to backend ports
- Useful for independent debugging and development
- Database shared across all services

### Service Ports & API Routes

| Service | Docker Route | Local Port | Purpose |
|---------|---|---|---------|
| Auth Service | `/auth/` | 7500 | JWT authentication & role-based redirects |
| TDMS Backend | `/tdms-api/` | 7250 | Test data CRUD operations |
| TCE Backend | `/api/` | 7000 | Test run execution & analysis |
| Interface Manager | (internal) | 8000 | Browser automation & LLM interactions |
| TCE Dashboard Frontend | `/` | 3000 | Test orchestration UI |
| TDMS Frontend | `/tdms/` | 8080 | Test data management UI |
| NGINX Proxy | - | 80/443 | Reverse proxy for all services (Docker only) |

## Core Components

| Component | Path | Tech Stack | Purpose |
|---|---|---|---|
| **TDMS Frontend** | `src/app/TDMS/front-end` | React + TypeScript + Vite, Radix UI, Tailwind CSS | Web UI for CRUD operations on test data entities (test cases, strategies, prompts, metrics, etc.) |
| **TDMS Backend** | `src/app/TDMS/back-end` | FastAPI, SQLAlchemy | REST APIs for test data management; v1 (legacy) and v2 (new) endpoints; JWT token validation |
| **TCE Dashboard Frontend** | `src/app/TestCaseExecutorDashboard/front-end` | React + TypeScript + CRA, React Bootstrap | Test run orchestration UI with live status tracking, WebSocket updates, analysis trigger, and report download |
| **TCE Dashboard Backend** | `src/app/TestCaseExecutorDashboard/back-end` | FastAPI, SQLAlchemy | Test run execution engine, filtering/analysis APIs, report generation, WebSocket push server (`/ws/test-run`) |
| **Auth Service** | `src/app/auth_service` | FastAPI | Central authentication authority; JWT token issuance/refresh/logout; role-based redirects (Admin/Manager → Dashboard, Curator/Viewer → TDMS) |
| **Interface Manager** | `src/app/interface_manager` | FastAPI, Selenium | Browser automation bridge for test execution; WhatsApp Web interaction; LLM API integration (OpenAI, Gemini, Sarvam AI); conversation & chat history management |
| **Shared Library** | `src/lib/` | Python | ORM abstractions, Interface Manager REST client, strategy logic, data utilities |

## Shared Data Model Scope

Both TDMS and dashboard operate on common entities and run records.

- TDMS core entities: test cases, targets, prompts, responses, strategies, domains, languages, test plans, metrics, LLM prompts
- Dashboard execution entities: test runs, run details, conversations, timelines, evaluation summaries

## Inter-Component Communication

```
1. Authentication Flow:
   User Login → Auth Service → JWT Token → Frontend State
   ↓
   All API requests include JWT in headers
   Backend validates via JWT middleware

2. Test Execution Flow:
   TDMS creates test plans/cases
   ↓
   Dashboard Frontend initiates test run
   ↓
   TCE Backend fetches test config from shared Database
   ↓
   TCE Backend invokes Interface Manager client
   ↓
   Interface Manager executes prompts via browser/LLM
   ↓
   Results → shared Database
   ↓
   Dashboard Frontend receives updates via WebSocket

3. Data Access Pattern:
   All services → MariaDB/SQLite (shared persistent layer)
   No direct service-to-service API calls (except TCE→Interface Manager)
```

## Why The Split Exists

### Separation of Concerns

- **TDMS** optimizes for **data governance and curation** — structured interfaces for managing test entities with validation and consistency
- **Dashboard** optimizes for **execution, monitoring, and post-run analysis** — dynamic orchestration with real-time feedback and complex analytics
- **Auth Service** ensures a **unified login boundary** across both applications with role-based access control
- **Interface Manager** abstracts **browser automation and LLM interactions** away from the main test execution pipeline

### Microservices Benefits

1. **Independent Scaling**: Track test execution load separately from data management load
2. **Technology Choices**: TDMS uses Vite (faster bundling), Dashboard uses CRA (broader ecosystem)
3. **API Versioning**: TDMS supports v1 & v2 endpoints for backwards compatibility during migrations
4. **Real-time Capabilities**: Dashboard WebSocket (`/ws/test-run`) enables live test monitoring without polling
5. **Extensible Browser Automation**: Interface Manager can be scaled independently and easily replaced with alternative automation frameworks
6. **Central Authentication**: Auth Service acts as the single source of truth for user identity and roles across all services
