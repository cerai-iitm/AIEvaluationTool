# UI

This section documents the full application UI: TDMS (Test Data Management System), the Test Case Execution Dashboard, authentication, roles, APIs, and local non-Docker setup.

TDMS is used to curate and manage evaluation data. The dashboard is used to execute runs, monitor progress, and review analysis outputs.


## What This Section Covers

- end-to-end local setup for TDMS, dashboard, auth service, and interface manager
- both frontend run modes (with and without NGINX)
- system architecture and component responsibilities
- authentication flow and role-based access
- TDMS module usage and dashboard run workflows
- key API endpoints and troubleshooting guidance

## Chapters

- [Setup](./setup.md)
- [Architecture And Components](./architecture_and_components.md)
- [Authentication And Roles](./authentication_and_roles.md)
- [TDMS Dashboard Manual](./tdms_dashboard_manual.md)
- [Test Runs Manual](./test_runs_manual.md)
- [Run Configuration Manual](./run_configuration_manual.md)
- [Analysis And Run Details Manual](./analysis_and_run_details_manual.md)
- [API Reference](./api_reference.md)
- [Troubleshooting](./troubleshooting.md)

## Typical Operator Flow

- Sign in through the centralized auth service.
- Prepare and maintain test data in TDMS.
- Move to the dashboard and start or continue test runs.
- Analyse completed runs and download reports.
- Use TDMS and dashboard history views for audit and review.
