# main.py

from routers import common, chat_router
from fastapi import FastAPI

app = FastAPI(title="LLM Evaluation Suite - Interface Manager")

# Common routes (login, logout, chat, config)
app.include_router(common.router)

# Chat route (with embedded UI handling)
app.include_router(chat_router.router)

# main driver
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=16000, reload=True)
