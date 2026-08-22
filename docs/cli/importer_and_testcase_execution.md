# Importer And Testcase Execution

This page documents the execution portion of the CLI workflow: importing evaluation data, starting Interface Manager, listing available plans and metrics, and running testcases against the configured target.

All commands below assume you are running them from the repository root and using the shared `config.json`.

## Import Test Data Into The Database

Before running evaluations, import the datapoints and related evaluation assets into the configured database.

```bash
python3 src/app/importer/main.py --config "config.json"
```

For deeper database-level logging during import, use:

```bash
python3 src/app/importer/main.py --config "config.json" --orm-debug
```

### Importer CLI Arguments

- `--config`: Path to the shared CLI configuration file. In the current workflow, use the repository-level `config.json`.
- `--orm-debug`: Enables ORM-level debug logging for database operations.

Expected result:

![Importing datapoints to database](../../screenshots/importing%20data%20to%20database.png)

## Start Interface Manager

The Interface Manager is responsible for handling communication with API, WhatsApp, and web application targets.

```bash
python3 src/app/interface_manager/main.py
```

Expected result:

![Interface Server Running](../../screenshots/interface_manager_running.png)

## Configure The Test Case Executor

Before running the executor, update the repository-level `config.json` with the correct `db`, `target`, and `interface_manager` values.

The testcase executor works as both a discovery tool and an execution tool. In practice, it is useful to inspect plans, metrics, targets, and previous runs before starting a new execution.

## Review Available Executor Options

```bash
python3 src/app/testcase_executor/main.py --config "config.json" -h
```

Reference:

![Arguments available in Testcase Executor](../../screenshots/arguments%20of%20testcase%20executor.png)

### Test Case Executor CLI Arguments

- `--config` or `-c`: Path to the shared CLI configuration file. Use the repository-level `config.json`.
- `--get-config-template` or `-T`: Prints a template configuration file for reference.
- `--get-plans` or `-P`: Lists available test plans.
- `--get-metrics` or `-M`: Lists available evaluation metrics.
- `--get-testcases` or `-C`: Lists testcases for a specific test plan or all testcases.
- `--get-targets` or `-G`: Lists all configured target applications.
- `--get-runs` or `-N`: Lists previous execution runs.
- `--testplan-id` or `-p`: Selects the test plan to execute.
- `--testcase-id` or `-t`: Restricts execution to a specific testcase.
- `--metric-id` or `-m`: Restricts execution to a specific metric.
- `--max-testcases` or `-n`: Limits how many testcases are executed. Default is `10`.
- `--run-name` or `-r`: Assigns a custom run name.
- `--run-continue` or `-R`: Continues an existing run using the specified run name.
- `--execute` or `-e`: Enables execution mode.
- `--verbosity` or `-v`: Sets logging verbosity from `0` to `5`. Default is `5`.
- `--language-strict` or `-l`: Enables strict language matching during testcase selection.
- `--domain-strict` or `-d`: Enables strict domain matching during testcase selection.

## List Available Test Plans

```bash
python3 src/app/testcase_executor/main.py --config "config.json" --get-plans
```

Reference:

![Plans](../../screenshots/get_plans.png)

## List Available Metrics

```bash
python3 src/app/testcase_executor/main.py --config "config.json" --get-metrics
```

Reference:

![Metrics](../../screenshots/get_metrics.png)

## List Available Testcases

If you want to inspect testcase availability before executing a run, use:

```bash
python3 src/app/testcase_executor/main.py --config "config.json" --get-testcases
```

This is useful when you want to scope execution more precisely with `--testcase-id`.

## List Available Targets

To inspect configured target applications:

```bash
python3 src/app/testcase_executor/main.py --config "config.json" --get-targets
```

This output helps confirm the execution interface, target type, and domain before running a plan.

## List Existing Runs

To inspect existing runs before creating or continuing one:

```bash
python3 src/app/testcase_executor/main.py --config "config.json" --get-runs
```

The returned run name can be reused with `--run-continue` if you want to resume execution.

## Execute Testcases

```bash
python3 src/app/testcase_executor/main.py \
  --testplan-id <testplan-id> \
  --testcase-id <testcase-id> \
  --metric-id <metric-id> \
  --max-testcases <max-testcases> \
  --config "config.json" \
  --execute
```

Replace the placeholders with values relevant to the test run you want to execute.

### Execution Constraints

`--testplan-id` is mandatory for execution. You can optionally add `--testcase-id` or `--metric-id` to narrow the run.

At minimum, one of these combinations should be used:

- `--testplan-id`
- `--testplan-id` with `--testcase-id`
- `--testplan-id` with `--metric-id`

### Common Execution Examples

Basic execution:

```bash
python3 src/app/testcase_executor/main.py --config "config.json" --testplan-id 1 --execute
```

Custom run name:

```bash
python3 src/app/testcase_executor/main.py --config "config.json" --testplan-id 1 --run-name "custom_run" --execute
```

Strict filtering:

```bash
python3 src/app/testcase_executor/main.py --config "config.json" --testplan-id 1 --language-strict --domain-strict --execute
```

Continue an existing run:

```bash
python3 src/app/testcase_executor/main.py --config "config.json" --testplan-id 1 --run-continue --run-name "previous_run_name" --execute
```

Expected runtime view:

![TEM Running](../../screenshots/Testcase_execution_manager_running.png)

If the target uses browser or WhatsApp interaction, the live interface may appear as:

![Interface](../../screenshots/Interface.jpg)

## What Happens During Execution

The executor:

- reads the configured test plan
- selects matching metrics and testcases
- sends prompts to the target through Interface Manager
- stores returned responses
- prepares the run for downstream analysis

The generated run name is important and should be preserved, because it is used again during analysis and report generation.

## Troubleshooting Notes

- if Interface Manager is unreachable, verify it is running before starting the executor
- if browser automation fails, re-check ChromeDriver compatibility and XPath mappings
- if plans or metrics are missing, verify the importer step completed successfully
- if database lookups fail, re-check the `db` section in the shared `config.json`
