from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import suites, prompts, runs, dashboard

app = FastAPI(title="EvalBoard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(suites.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}


# Serve the React frontend when running inside Docker (dist/ will exist).
# In local dev the dist/ folder is absent, so this block is skipped.
_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/assets", StaticFiles(directory=str(_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        candidate = _dist / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_dist / "index.html"))
