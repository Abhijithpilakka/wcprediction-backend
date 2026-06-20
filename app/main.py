from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.routers import auth, matches, predictions, leaderboard, admin

settings = get_settings()

app = FastAPI(
    title="WC2026 Predictor API",
    description="Backend for the FIFA World Cup 2026 prediction platform",
    version="1.0.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(matches.router)
app.include_router(predictions.router)
app.include_router(leaderboard.router)
app.include_router(admin.router)


# ─── Health check ────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}
