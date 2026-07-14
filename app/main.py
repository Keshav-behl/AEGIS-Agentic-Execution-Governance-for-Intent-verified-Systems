from fastapi import FastAPI

from app import config  # noqa: F401  (import triggers required-var validation on startup)

app = FastAPI(title="AEGIS")


@app.get("/health")
def health():
    return {"status": "ok"}
