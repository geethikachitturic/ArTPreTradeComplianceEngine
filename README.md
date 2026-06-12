# ArT — Pre-Trade Booking Model Controls

AI-enhanced pre-trade compliance controls engine enforcing **Regulation T** and **FINRA Rule 4210 (2026 amendments)** for Equity and Fixed Income products.

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | Python 3.12 + FastAPI + SQLAlchemy |
| Database | PostgreSQL 16 |
| Containerisation | Docker Compose |

---

## Quick Start

### Option A — Docker (recommended, one command)

```bash
docker-compose up --build
```

Then open http://localhost:5173 and seed the database:

```bash
docker exec art_backend python seed_data.py
```

---

### Option B — Run locally

#### 1. Start PostgreSQL

```bash
docker-compose up db -d
```

#### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed_data.py        # loads users + rules
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

#### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

---

## Platform Views

| View | URL | Role |
|------|-----|------|
| Trade Generator (Stub 1) | /stub1 | Demo / testing |
| Trader Entry | /trader | Trader |
| Approvals (Stub 2) | /approvals | Supervisor |
| Rules Manager | /rules | Controls Team |
| MI Dashboard | /dashboard | Management |
| Audit Log | /audit | Compliance |

---

## ArT Decision Outcomes

| Outcome | Meaning |
|---------|---------|
| **Clean Pass** | No rules triggered. Trade proceeds. |
| **Soft Block** | Warning issued. Trader acknowledges and can proceed. |
| **Hard Block** | Trade rejected. Regulatory hard limit — no override path. |
| **Hard Block with Override** | Trade blocked pending supervisory approval (Stub 2). |

---

## Regulatory Coverage

- **Regulation T (12 CFR Part 220):** 50% initial margin for equity purchases, 150% collateral for short sales, full payment for cash accounts, fixed income margin by credit grade.
- **FINRA Rule 4210 (2026 amendments):** Intraday Margin Level (IML) computation, intraday margin deficit framework, safe harbour thresholds, 90-day freeze enforcement, portfolio margin sub-$5M check. PDT regime eliminated.
