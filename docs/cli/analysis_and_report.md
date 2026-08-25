# Analysis And Report

This page explains the final stages of the CLI workflow: response analysis and report generation.

All commands below assume you are running them from the repository root and using the shared `config.json`.

## Identify The Run Name

After testcase execution completes, collect the `run-name` from one of the following places:

- testcase executor logs
- test runs table in the database

The same `run-name` is used for both analysis and reporting.

If the run name is not available in executor logs, retrieve it through the testcase executor:

```bash
python3 src/app/testcase_executor/main.py --config "config.json" --get-runs
```

Direct database queries can also be used as a fallback.

SQLite:

```bash
sqlite3 data/AIEvaluationData.db \
  "SELECT run_id, run_name, created_at FROM test_runs ORDER BY created_at DESC LIMIT 5;"
```

MariaDB:

```bash
mysql -u aiet_user -p aievaluationtool \
  -e "SELECT run_id, run_name, created_at FROM test_runs ORDER BY created_at DESC LIMIT 5;"
```

## Run Response Analysis

Start the analysis step from the repository root:

```bash
python3 src/app/response_analyzer/analyze.py --config "config.json" --run-name <run-name>
```

During this step, the analyzer processes collected responses using the configured evaluation strategies.

### Analyzer CLI Arguments

- `--config`: Path to the shared CLI configuration file. Use the repository-level `config.json`.
- `--get-config-template` or `-T`: Prints a template configuration file.
- `--verbosity` or `-v`: Sets logging verbosity from `0` to `5`. Default is `5`.
- `--run-name` or `-r`: Name of the execution run to analyze.
- `--force` or `-f`: Forces re-evaluation of runs that already have analysis data.
- `--retry-failed` or `-rf`: Re-runs only failed analysis cases.
- `--detail-ids` or `-di`: Comma-separated run detail IDs to analyze. If omitted, all details in the run are analyzed.

### Analysis Examples

Re-run failed analysis cases:

```bash
python3 src/app/response_analyzer/analyze.py --config "config.json" --run-name "doodle-accepting-pascal-nibh" --retry-failed --force
```

Re-analyze specific run detail IDs:

```bash
python3 src/app/response_analyzer/analyze.py --config "config.json" --run-name "doodle-accepting-pascal-nibh" --detail-ids 2,4,5,6 --force
```

Operational note:

- analysis is idempotent by default
- use `--force` only when you intentionally want to overwrite existing results

Reference:

![Response Analysis Image](../../screenshots/Response_analyzer_running.png)

## Generate The Evaluation Report

Use the same `run-name` and the same shared config file to create the final report:

```bash
python3 src/app/response_analyzer/report.py --config "config.json" --run-name <run-name> --get-report
```

### Report Generator CLI Arguments

- `--config`: Path to the shared CLI configuration file. Use the repository-level `config.json`.
- `--get-config-template` or `-T`: Prints a template configuration file.
- `--verbosity` or `-v`: Sets logging verbosity from `0` to `5`. Default is `5`.
- `--get-runs` or `-N`: Lists available execution runs.
- `--run-name` or `-r`: Run name for which the report should be generated.
- `--force` or `-f`: Forces report generation even if a report already exists.
- `--get-report` or `-R`: Triggers report generation.

### Reporting Notes

- the `--run-name` must match the analyzed run
- report generation is non-destructive by default
- use `--force` only when you want to replace an existing report

Reference:

![Evaluation Report](../../screenshots/report_generation.png)

## Output Of The Report

The report stage is intended to produce detailed evaluation output, including metric-level results and summary information for the executed run.

## Common Checks

- confirm the analysis step completed successfully before running report generation
- confirm the `run-name` matches the executed run
- verify the shared `config.json` points to the same database used during execution
