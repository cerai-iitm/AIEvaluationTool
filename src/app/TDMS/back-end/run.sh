#!/bin/bash
# Script to run the FastAPI application

# Activate virtual environment
source venv/bin/activate

# Run the application with uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

