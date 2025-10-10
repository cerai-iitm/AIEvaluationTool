# main.py

from routers import common, chat_router, api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LLM Evaluation Suite - Interface Manager")

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
