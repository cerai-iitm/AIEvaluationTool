import uvicorn
import logging
# from config.logger import get_logger
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database.database import init_db, seed_users
from api.v1.endpoints import auth, dashboard, testCase
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.add_middleware(AuthMiddleware)


app.include_router(auth.auth_router, tags=["Authentication"])
app.include_router(dashboard.dashboard_router, tags=["Dashboard"])
app.include_router(testCase.testcase_router, tags=["Test Cases"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

