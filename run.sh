#!/bin/bash

cd TestCaseExecutionManager/src
python TestCaseExecutionManager.py --test_plan_id T1 --test_case_count 2
cd ..
cd ..
python ResponseAnalyzer/src/ResponseAnalyzer.py