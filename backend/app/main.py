from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import art, audit, overrides, reports, rules, stubs, users

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ArT — Pre-Trade Booking Model Controls",
    description=(
        "AI-enhanced pre-trade compliance controls engine. "
        "Enforces Regulation T and FINRA Rule 4210 (2026 amendments) "
        "for Equity and Fixed Income products."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(art.router)
app.include_router(rules.router)
app.include_router(overrides.router)
app.include_router(stubs.router)
app.include_router(reports.router)
app.include_router(audit.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ArT Pre-Trade Controls Engine"}
