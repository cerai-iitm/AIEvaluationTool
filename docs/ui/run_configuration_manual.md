# Run Configuration User Manual

Use this page to configure and execute new runs or continue existing runs.

## A. Create New Test Run

- Route: `/create-test-run`
- Open from: `New Test Run` button on Test Runs page

![Create a new test run](../../screenshots/TRDB_add_test_run.png)

### Field Locations And Behavior

- `Test Run Name`: optional custom name
- `Target`: required
- `Test Plan`: required
- `Metric`: enabled after selecting `Test Plan`
- `Test Case Name`: enabled after selecting `Test Plan`
- `Max test cases`: execution cap
- `Domain` and `Language`: loaded after selecting `Target`

### Start Action

- Click `Start Run` to execute
- Progress loop shows stages:
  - `Prepare`
  - `Finding elements`
  - `Execute`
  - `Store`

### Stop Action

- While a run is in progress, a `Stop Run` button is shown in place of `Start Run`
- Click `Stop Run` to cancel the in-progress run
- Calls `POST /test-runs/{run_id}/stop` on the dashboard backend

### Watching A Run Live (View Test Execution)

For `WhatsApp` and `WebApp` targets, the tool drives a real browser. While the run is in progress, a **View Test Execution** link appears under the progress loop. It opens that run's browser in a new tab, so you can watch it log in, type prompts and read replies.

- The link appears only once the run's browser session has started. It is not shown for `API` targets.
- Each run has its own browser, so two people running at the same time each see their own run.
- All test cases of a run use the same browser, so the view stays the same for the whole run.
- For WhatsApp targets, scan the QR code in this view when the run starts.
- After the run finishes, the browser is closed and the view no longer shows anything.
- If the browser restarts during a run, an already open view keeps showing the old one. Open the link again.

If a run fails at login, typing or reading the reply, this view shows where it stops. See [Web App Target Configuration](./web_app_target_configuration.md) to fix the selectors.

## B. Continue Existing Run

- Route: `/continue-run/:runName`
- Open from: `Continue` action on Test Runs page or Run Details page

### Screen Sections

- `Run Details` accordion:
  - target
  - status
  - start/end timestamps
  - metrics grouped by plan
- `Use Existing or Modify Setup` section:
  - test plan
  - metric
  - testcase name
  - max test cases
  - domain/language

### Continue Action

- Click `Start Run` inside continue configuration
- Same execution loop and progress behavior applies
- Same `Stop Run` control is available while the continued run is in progress
- Same **View Test Execution** link is shown for `WhatsApp` and `WebApp` targets; see [Watching A Run Live](#watching-a-run-live-view-test-execution)

## Recommended Operator Sequence

1. Use `Create New Test Run` for first execution.
2. Use `Continue Run` for extending or retrying with narrower scope.
3. Move to analysis after responses are collected.
