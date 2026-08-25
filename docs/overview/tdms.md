# TDMS

The Test Data Management System, or TDMS, is the application used to manage the structured evaluation data that powers the larger AI Evaluation Tool workflow.

## What TDMS Does

TDMS provides a centralized place to create, organize, and maintain the data required for evaluation. This includes testcases, prompts, responses, strategies, and related metadata. Instead of treating evaluation data as a scattered set of files, TDMS gives teams an operational interface for managing that information in a more controlled way.

## Why It Exists In The Platform

The evaluation workflow depends on high-quality test assets. TDMS supports that need by making it easier to:

- maintain curated testcase collections
- organize evaluation inputs and supporting metadata
- manage data through a web-based interface
- support collaborative workflows with role-based access

In other words, TDMS strengthens the data foundation of the whole evaluation pipeline.

## Architecture Summary

TDMS follows a three-tier application model:

- React and TypeScript frontend
- FastAPI backend
- SQLite or MariaDB database

This structure keeps the data-management concerns separate from the execution and analysis components of the CLI workflow.

## How TDMS Relates To The Core Workflow

While the CLI handles execution and analysis, TDMS focuses on preparing and maintaining the data that those processes rely on. Teams can use TDMS to improve data quality, organize evaluation assets, and keep their testing inputs manageable as coverage grows over time.

## Typical Use Cases

- managing large collections of testcases
- reviewing and updating prompts and responses
- organizing evaluation strategies and metadata
- supporting different user roles in a shared testing environment

## Related Sections

- [UI documentation](../ui/index.md)
- [Docker Setup](../docker_setup/index.md)
