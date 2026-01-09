import os
import sys

# Add top-level src directory (which contains the 'lib' package) to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import logging
from contextlib import asynccontextmanager

import uvicorn
from api.v1.endpoints import (
    auth,
    dashboard,
    #     domain,
    #     language,
    #     llmPrompt,
    #     prompt,
    #     response,
    #     strategy,
    #     target,
    #     testCase,
    users,
)
from api.v2.endpoints import (
    domain as domain_v2,
)
from api.v2.endpoints import (
    language as language_v2,
)
from api.v2.endpoints import (
    llmPrompt as llm_prompt_v2,
)
from api.v2.endpoints import (
    prompt as prompt_v2,
)
from api.v2.endpoints import (
    response as response_v2,
)
from api.v2.endpoints import (
    strategy as strategy_v2,
)
from api.v2.endpoints import (
    target as target_v2,
)
from api.v2.endpoints import (
    testCase as testCase_v2,
)
from database.database import init_db, seed_users

# from config.logger import get_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles as static_files
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
    title="AIEvaluationTool",
    description="API for AIEvaluationTool Data Management Application",
    version="1.0.0",
    lifespan=lifespan,
)
# static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))


# app.mount("/static", static_files(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(AuthMiddleware)


app.include_router(auth.auth_router, tags=["Authentication"])
app.include_router(dashboard.dashboard_router, tags=["Dashboard"])
# app.include_router(testCase.testcase_router, tags=["Test Cases"])
# app.include_router(response.response_router, tags=["Responses"])
# app.include_router(strategy.strategy_router, tags=["Strategies"])
# app.include_router(prompt.prompt_router, tags=["Prompts"])
# app.include_router(llmPrompt.llmPrompt_router, tags=["LLM Prompts"])
# app.include_router(target.target_router, tags=["Targets"])
# app.include_router(language.language_router, tags=["Languages"])
# app.include_router(domain.domain_router, tags=["Domains"])
app.include_router(users.users_router, tags=["Users"])
app.include_router(testCase_v2.testcase_router, tags=["Testcase_v2"])
app.include_router(target_v2.target_router, tags=["Target_v2"])
app.include_router(domain_v2.domain_router, tags=["Domain_v2"])
app.include_router(language_v2.language_router, tags=["Language_v2"])
app.include_router(llm_prompt_v2.llm_prompt_router, tags=["LLM_Prompt_v2"])
app.include_router(prompt_v2.prompt_router, tags=["Prompt_v2"])
app.include_router(response_v2.response_router, tags=["Response_v2"])
app.include_router(strategy_v2.strategy_router, tags=["Strategy_v2"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
