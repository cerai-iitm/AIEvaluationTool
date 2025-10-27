"""Interface Manager FastAPI application entrypoint.

When this file is executed directly (python3 main.py) the interpreter's
import path doesn't include the repository `src/` directory. The project
uses top-level imports like `lib...` and `app...` which live under
`src/`. Insert `src/` at the front of sys.path so those absolute imports
work without requiring the caller to set PYTHONPATH.
"""
import os
import sys

# Ensure the project's `src` directory is on sys.path so top-level imports
# like `lib` resolve when running this module directly.
THIS_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from routers import common, chat_router, api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from database import init_db, seed_users
from contextlib import asynccontextmanager

app = FastAPI(title="LLM Evaluation Suite - Interface Manager")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    init_db()
    seed_users()
    yield
    logger.info("Shutting down application...")



# Enable CORS so the Front-end_AIEvaluationTool can call these APIs from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Common routes (login, logout, chat, config)
app.include_router(common.router)

# Chat route (with embedded UI handling)
app.include_router(chat_router.router)

# Public API for frontend consumption
app.include_router(api.router)

# main driver
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
