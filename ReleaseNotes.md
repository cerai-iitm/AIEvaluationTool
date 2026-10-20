### **Conversational AI Evaluation Tool - Version 2.1.0**

#### **Description**:

Version 2.1.0 is a scalability and deployment release built on top of 2.0.1. It introduces Redis-backed shared state so that backend services can run as multiple replicas, adds Docker Swarm stack deployment, and brings per-run Selenium Grid sessions with live browser view for web-app targets. The backend services now ship as a single consolidated image, and the evaluation metrics were made more reliable through run-level statistics and richer NLP metric details. A set of TDMS and Dashboard fixes rounds out the release.

#### **New Features**

- **Redis-Backed Shared State & Real-Time Updates**

    Redis was added to the stack (with a healthcheck) and integrated into the backend services for shared state management. Analysis job handling was refactored around it, and a WebSocket pub/sub listener now delivers real-time run updates correctly across multiple backend replicas. Ollama client connection timeouts were also improved.

- **Docker Swarm Stack Deployment**

    A swarm-compatible `stack-compose.yml` was added for clustered deployment, with configurable replica counts for backend services and Selenium nodes. Ollama parallelism and context length are tunable for higher-throughput judge-model inference, and nginx upstream definitions were reworked for load balancing.

- **Per-Run Selenium Sessions & Live View**

    `selenium-browser` was replaced with a Selenium Grid (`selenium-hub` plus nodes). Each test run now gets its own session via a `run_id`-aware API. The frontend fetches session-specific live-view links, and noVNC access to sessions is proxied through the interface manager, so a run's browser can be watched live.

- **Generic Web-App Handler for TDMS UI Targets**

    Web app handlers now support generic handling of TDMS UI targets. Users can set the XPath configurations for login and chat themselves, so a new web-app target can be added without code changes.

- **Consolidated Backend Image**

    The Dockerfile and compose files now build the interface-manager, auth-service, app-backend, sarvam-ai and tdms-backend services from a single shared `runtime-base` image. This simplifies builds and deployment, and the unused sarvam-ai upstream and internal load-balancer configuration in `nginx.conf` was removed.

- **Health Check Endpoint**

    A health check endpoint was added, and the related middleware was updated.

#### **Improvements & Fixes**

- **Evaluation Metrics**: metrics now use run-level statistics, and database connection handling in the strategies was streamlined. Reliability scoring was improved across several strategies. BLEU and METEOR issues were fixed, and both now report additional information. NER now uses spaCy for normal text responses, and the spaCy model is downloaded automatically if it is missing.
- **Test Runs**: during Continue Run, existing conversation data is now overridden in `execute_testcases`. The shared data volume is now mounted for the test run service.
- **TDMS**: fixed the test case table loading issues and the import UI bug. Fixed the loading dialogue box, filters that did not work, and a bug in the Target Add dialogue. Test case filtering and pagination logic was moved out of the component.
- **Dashboard**: the Analysis component was simplified by removing the unused `analysisCurrent` state and simplifying the completed-cases calculation.
- **UI**: button styles were refactored and the button components moved to a new variant. The accent colors were adjusted for consistency.
- **Configuration & Infrastructure**: MariaDB configuration was updated and the Redis URL now adapts to Docker settings. A logging string-formatting bug was fixed, and the `redis` dependency was added to `requirements.txt`. The unused warm-up service was commented out in the stack file.
- **Documentation**: updated the architecture documentation and user manual, and added a Docker architecture image.