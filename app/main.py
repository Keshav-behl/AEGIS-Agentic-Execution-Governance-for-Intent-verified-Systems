from fastapi import FastAPI

from app import config  # noqa: F401  (import triggers required-var validation on startup)
from app.approval.approval_routes import router as approval_router

app = FastAPI(title="AEGIS")
app.include_router(approval_router)


@app.get("/health")
def health():
    return {"status": "ok"}
