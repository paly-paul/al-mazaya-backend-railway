"""
Database initialisation script.
Run standalone: python migrations/init_db.py
Or called from main.py on startup.
"""
import sys
import os
from pathlib import Path

# Allow running from any directory
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

# Default DATABASE_URL for standalone runs (override via env var)
default_db_path = backend_dir / "data" / "mazaya_fm.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{default_db_path.as_posix()}")

from database import engine, Base, create_all_tables

# Import all models to register them with Base.metadata
from models import (  # noqa: F401
    Lead,
    Ticket,
    WorkOrder,
    Vendor,
    ChatMessage,
    ChatSession,
    Briefing,
)


def init_db():
    print("Creating database tables...")
    create_all_tables()
    print("Database tables created successfully.")


def seed_sample_vendors():
    """Insert a few sample vendors so dispatch works out of the box."""
    import json
    from database import SessionLocal
    from models import Vendor

    db = SessionLocal()
    try:
        existing = db.query(Vendor).count()
        if existing > 0:
            print(f"Database already has {existing} vendors — skipping seed.")
            return

        sample_vendors = [
            {
                "company_name": "Gulf HVAC Solutions",
                "categories": json.dumps(["hvac", "electrical", "medical_gas"]),
                "towers_covered": json.dumps(["all"]),
                "contact_name": "Ahmed Al-Rashid",
                "phone": "+965-9999-1001",
                "email": "ops@gulfhvac.kw",
                "trade_licence": "KW-TL-10001",
                "score": 92.0,
                "status": "active",
                "jobs_completed": 145,
            },
            {
                "company_name": "Kuwait Plumb & Civil",
                "categories": json.dumps(["plumbing", "civil"]),
                "towers_covered": json.dumps(["all"]),
                "contact_name": "Mohammed Yusuf",
                "phone": "+965-9999-1002",
                "email": "info@kwplumb.kw",
                "trade_licence": "KW-TL-10002",
                "score": 85.0,
                "status": "active",
                "jobs_completed": 98,
            },
            {
                "company_name": "Al-Mazaya Cleaning Services",
                "categories": json.dumps(["cleaning", "pest"]),
                "towers_covered": json.dumps(["all"]),
                "contact_name": "Sara Al-Mutairi",
                "phone": "+965-9999-1003",
                "email": "cleaning@almazaya.kw",
                "trade_licence": "KW-TL-10003",
                "score": 88.0,
                "status": "active",
                "jobs_completed": 210,
            },
            {
                "company_name": "FireSafe Kuwait",
                "categories": json.dumps(["fire", "electrical"]),
                "towers_covered": json.dumps(["all"]),
                "contact_name": "Khalid Al-Hamdan",
                "phone": "+965-9999-1004",
                "email": "contact@firesafekw.com",
                "trade_licence": "KW-TL-10004",
                "score": 90.0,
                "status": "active",
                "jobs_completed": 67,
            },
            {
                "company_name": "Express Lift Maintenance",
                "categories": json.dumps(["lift"]),
                "towers_covered": json.dumps(["all"]),
                "contact_name": "Ali Hassan",
                "phone": "+965-9999-1005",
                "email": "ali@expresslift.kw",
                "trade_licence": "KW-TL-10005",
                "score": 87.0,
                "status": "active",
                "jobs_completed": 34,
            },
            {
                "company_name": "Mazaya Facilities Group",
                "categories": json.dumps(["hvac", "electrical", "plumbing", "civil", "cleaning", "pest", "other"]),
                "towers_covered": json.dumps(["all"]),
                "contact_name": "Operations Center",
                "phone": "+965-9999-1000",
                "email": "fm@mazayagroup.kw",
                "trade_licence": "KW-TL-10000",
                "score": 80.0,
                "status": "active",
                "jobs_completed": 500,
            },
        ]

        for v_data in sample_vendors:
            vendor = Vendor(**v_data)
            db.add(vendor)
        db.commit()
        print(f"Seeded {len(sample_vendors)} sample vendors.")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    seed_sample_vendors()
