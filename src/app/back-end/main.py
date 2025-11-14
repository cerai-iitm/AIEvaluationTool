import sys
import os
# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import uvicorn
import logging
# from config.logger import get_logger
from fastapi import FastAPI 
from fastapi.staticfiles import StaticFiles as static_files
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database.database import init_db, seed_users
from api.v1.endpoints import auth, dashboard, testCase, response, strategy, prompt, llmPrompt, target,language, users
from middleware.middleware import AuthMiddleware




logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    init_db()
    seed_users()
    yield
    logging.info("Shutting down application...")


app = FastAPI(
    title = 'AIEvaluationTool',
    description = 'API for AIEvaluationTool Data Management Application',
    version = '1.0.0',
    lifespan=lifespan
)
# static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))



# app.mount("/static", static_files(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
# app.add_middleware(AuthMiddleware)


app.include_router(auth.auth_router, tags=["Authentication"])
app.include_router(dashboard.dashboard_router, tags=["Dashboard"])
app.include_router(testCase.testcase_router, tags=["Test Cases"])
app.include_router(response.response_router, tags=["Responses"])
app.include_router(strategy.strategy_router, tags=["Strategies"])
app.include_router(prompt.prompt_router, tags=["Prompts"])
app.include_router(llmPrompt.llmPrompt_router, tags=["LLM Prompts"])
app.include_router(target.target_router, tags=["Targets"])
app.include_router(language.language_router, tags=["Languages"])
app.include_router(users.users_router, tags=["Users"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

