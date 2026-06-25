# ArT Pre-Trade Compliance Engine — Setup Guide

This guide is written for non-developers. Follow the steps in order and you should have the app running in under 10 minutes.

---

## What You Need Before Starting

Install these two things on your computer:

1. **Docker Desktop**
   - Mac: https://www.docker.com/products/docker-desktop/
   - Windows: same link above
   - After installing, open Docker Desktop and make sure it is running (you should see the Docker whale icon in your menu bar or taskbar)

2. **Git**
   - Mac: https://git-scm.com/download/mac
   - Windows: https://git-scm.com/download/win

---

## Step 1 — Download the App

Open **Terminal** (Mac) or **Command Prompt** (Windows) and type:

```
git clone https://github.com/YOUR_USERNAME/ArtPreTradeComplianceEngine.git
```

Then move into the project folder:

```
cd ArtPreTradeComplianceEngine
```

---

## Step 2 — Start the App

Run this single command:

```
docker compose up --build
```

The first time you run this it will take **5–10 minutes** as Docker downloads everything it needs. You will see a lot of text scrolling — this is normal.

When you see this line, the app is ready:

```
art_backend  | INFO:     Application startup complete.
```

---

## Step 3 — Load the Seed Data

The app needs some sample data to work with. Open a **second terminal window**, go to the project folder, and run:

```
cd ArtPreTradeComplianceEngine
docker exec art_backend python seed_data.py
```

You should see:
```
Seeded 13 users.
Seeded 13 rules.
Seed complete.
```

You only need to do this once.

---

## Step 4 — Open the App

Open your browser and go to:

```
http://localhost:5173
```

The app should be fully working. You can now explore all the features.

---

## Platform Views

| View | URL | Role |
|------|-----|------|
| Trade Generator (Stub 1) | http://localhost:5173/stub1 | Demo / testing |
| Trader Entry | http://localhost:5173/trader | Trader |
| Approvals (Stub 2) | http://localhost:5173/approvals | Supervisor |
| Rules Manager | http://localhost:5173/rules | Controls Team |
| MI Dashboard | http://localhost:5173/dashboard | Management |
| Audit Log | http://localhost:5173/audit | Compliance |

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

---

## Stopping the App

When you are done, go back to the terminal where the app is running and press:

```
Ctrl + C
```

To start it again next time (much faster, no need to rebuild):

```
docker compose up
```

---

## Troubleshooting

**Docker says "port already in use"**
Something else on your computer is using the same port. Restart Docker Desktop and try again.

**The page won't load at localhost:5173**
Wait another minute — the app may still be starting up. Check the terminal for the "Application startup complete" message.

**Buttons not working or errors on screen**
Make sure you ran the seed data command in Step 3. If you did and it still doesn't work, try:
```
docker compose down
docker compose up --build
```

**Everything is stuck or broken**
This resets everything and starts fresh (note: clears all data):
```
docker compose down -v
docker compose up --build
```
Then repeat Step 3 to reload the seed data.

---

*If you get stuck, feel free to raise a GitHub issue on this repository.*
