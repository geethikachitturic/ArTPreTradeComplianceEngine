# ArT Project — Claude Code Instructions

## Project Context
- **Product:** ArT (Automated Review Tool) — FINRA Rule 4210 (2026) and Regulation T pre-trade compliance engine
- **Role:** User is the Product Owner
- **Stack:** FastAPI (Python 3.9) backend · React/TypeScript frontend · SQLite via SQLAlchemy · Vite
- **Project path:** ~/Documents/AI_Study/finra4210/
- **Default doc save path:** ~/Documents/AI_Study/finra4210/ProjectRefDocs/

---

## Instruction 1 — Word Document Prompt
After providing an answer to any query, always ask the user:
> "Would you like me to save this answer to a Word document? If yes, please provide the file name and the folder path where you would like it saved."

Wait for the user's response before generating the document. If they provide a file name but no path, default to `~/Documents/AI_Study/finra4210/ProjectRefDocs/`.

---

## Instruction 2 — Word Document Formatting Standards
Every Word document generated must include the following:

1. **Page numbers** — centred in the footer, formatted as "Page X of Y"
2. **Table of Contents** — placed after the title page, before the first section
   - Must include page numbers
   - Must be hyperlinked (reader can click an entry to jump to that page)
   - Use the TOC field with flags: `TOC \o "1-3" \h \z \u`
   - Include a note instructing the user to right-click → "Update Field" → "Update entire table" when opening in Word to populate page numbers and hyperlinks
