# Al Mazaya Backend - Railway Deploy

Standalone FastAPI backend for the Mazaya FM chatbot, admin APIs, agent tools, scheduler, and local SQLite database.

## Run Locally

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Set `GROQ_API_KEY` in `.env`. `ALLOWED_ORIGINS=*` allows requests from any frontend origin. The default database is `sqlite:///./data/mazaya_fm.db`, which resolves inside this backend folder.

## Seed Demo Data

```powershell
.\.venv\Scripts\Activate.ps1
python seed_db.py
```

The backend auto-creates tables and basic vendors on startup. `seed_db.py` adds the larger demo dataset for dashboards and tests.

## Key Files

| File | Purpose |
| --- | --- |
| `.env` | Local backend secrets and runtime config |
| `.env.example` | Safe template for backend config |
| `main.py` | FastAPI app entry point |
| `config.py` | Reads backend-local `.env` |
| `database.py` | SQLAlchemy engine/session setup |
| `seed_db.py` | Optional demo data loader |

## URLs

```text
http://localhost:8000
http://localhost:8000/docs
http://localhost:8000/health
```
