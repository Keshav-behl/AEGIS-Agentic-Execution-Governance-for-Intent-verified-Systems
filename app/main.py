import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import config  # noqa: F401  (import triggers required-var validation on startup)
from app.api.routes import router as api_router
from app.approval.approval_routes import router as approval_router
from app.approval.sla import sweep_sla

SLA_SWEEP_INTERVAL_SECONDS = 15


async def _sla_sweep_loop():
    while True:
        await asyncio.sleep(SLA_SWEEP_INTERVAL_SECONDS)
        try:
            sweep_sla()
        except Exception:
            pass  # a transient sweep failure shouldn't take down the loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_sla_sweep_loop())
    yield
    task.cancel()


app = FastAPI(title="AEGIS", lifespan=lifespan)
app.include_router(approval_router)
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
