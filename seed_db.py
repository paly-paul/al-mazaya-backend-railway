#!/usr/bin/env python3
"""
seed_db.py - Populate the Mazaya FM database with realistic dummy data.

Run from the backend directory:
    python seed_db.py

Or from the repository root:
    python backend/seed_db.py
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow running from the backend folder or from the repository root.
script_dir = Path(__file__).resolve().parent
app_dir = script_dir
sys.path.insert(0, str(app_dir))

default_db_path = app_dir / "data" / "mazaya_fm.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{default_db_path.as_posix()}")

from database import SessionLocal, engine, Base

# Import all models so Base knows about them
from models.vendor import Vendor
from models.lead import Lead
from models.ticket import Ticket
from models.work_order import WorkOrder
from models.session import ChatSession
from models.message import ChatMessage

Base.metadata.create_all(bind=engine)

db = SessionLocal()

now = datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# 1. VENDORS  (6 vendors matching admin panel prototype data)
# ─────────────────────────────────────────────────────────────────────────────

VENDORS = [
    {
        "company_name": "Gulf HVAC Solutions",
        "categories": ["hvac"],
        "towers_covered": ["all"],
        "contact_name": "Mohammed Al-Rashidi",
        "phone": "+965-9900-1122",
        "email": "ops@gulfhvac.com.kw",
        "trade_licence": "TL-HVAC-20210045",
        "score": 92.0,
        "status": "active",
        "jobs_completed": 87,
    },
    {
        "company_name": "Al-Noor Electrical",
        "categories": ["electrical", "fire"],
        "towers_covered": ["Clinic III", "Clinic IV", "Clinic V"],
        "contact_name": "Faisal Al-Mutairi",
        "phone": "+965-9911-2233",
        "email": "dispatch@alnoor-elec.com.kw",
        "trade_licence": "TL-ELEC-20190078",
        "score": 88.0,
        "status": "active",
        "jobs_completed": 134,
    },
    {
        "company_name": "Gulf Plumb Co.",
        "categories": ["plumbing", "civil"],
        "towers_covered": ["all"],
        "contact_name": "Hassan Al-Enezi",
        "phone": "+965-9922-3344",
        "email": "service@gulfplumb.com.kw",
        "trade_licence": "TL-PLMB-20200112",
        "score": 79.0,
        "status": "active",
        "jobs_completed": 62,
    },
    {
        "company_name": "Medline Technical Services",
        "categories": ["medical_gas", "lift", "fire"],
        "towers_covered": ["Clinic VI Tower A", "Clinic VI Tower B", "Medical Centre"],
        "contact_name": "Dr. Khaled Boushehri",
        "phone": "+965-9933-4455",
        "email": "technical@medline.com.kw",
        "trade_licence": "TL-MED-20220033",
        "score": 95.0,
        "status": "active",
        "jobs_completed": 41,
    },
    {
        "company_name": "CleanPro Facilities",
        "categories": ["cleaning", "pest"],
        "towers_covered": ["all"],
        "contact_name": "Rania Al-Salam",
        "phone": "+965-9944-5566",
        "email": "manager@cleanpro.com.kw",
        "trade_licence": "TL-CLN-20230009",
        "score": 55.0,
        "status": "below_threshold",
        "jobs_completed": 28,
    },
    {
        "company_name": "Swift Signage & Displays",
        "categories": ["signage", "digital_display", "lighting"],
        "towers_covered": ["Clinic III", "Clinic IV", "Clinic V", "Clinic VI Tower A"],
        "contact_name": "Sara Al-Fahad",
        "phone": "+965-9955-6677",
        "email": "projects@swiftsignage.com.kw",
        "trade_licence": "TL-SGN-20210099",
        "score": 82.0,
        "status": "active",
        "jobs_completed": 19,
    },
]


def seed_vendors(db):
    existing = db.query(Vendor).count()
    if existing >= len(VENDORS):
        print(f"  Vendors: {existing} already exist, skipping.")
        return []

    vendor_objs = []
    for v in VENDORS:
        vendor = Vendor(
            company_name=v["company_name"],
            categories=json.dumps(v["categories"]),
            towers_covered=json.dumps(v["towers_covered"]),
            contact_name=v["contact_name"],
            phone=v["phone"],
            email=v["email"],
            trade_licence=v["trade_licence"],
            score=v["score"],
            status=v["status"],
            jobs_completed=v["jobs_completed"],
        )
        db.add(vendor)
        vendor_objs.append(vendor)
    db.flush()
    print(f"  Vendors: inserted {len(vendor_objs)}")
    return vendor_objs


# ─────────────────────────────────────────────────────────────────────────────
# 2. LEADS  (5 leads at different score tiers)
# ─────────────────────────────────────────────────────────────────────────────

LEADS = [
    {
        "name": "Dr. Aisha Al-Kandari",
        "phone": "+965-6600-1001",
        "specialty": "Dermatology",
        "clinic_size": "medium",
        "tower_preference": "Clinic IV",
        "budget_range": "1500-2500 KD/mo",
        "timeline": "within_1_month",
        "source": "web_chat",
        "score": 85.0,
        "tier": "hot",
        "status": "meeting_set",
        "assigned_to": "Ahmed K.",
    },
    {
        "name": "Dr. Yousef Al-Sabah",
        "phone": "+965-6600-1002",
        "specialty": "Orthopedics",
        "clinic_size": "large",
        "tower_preference": "Clinic VI Tower A",
        "budget_range": "2500-4000 KD/mo",
        "timeline": "1_3_months",
        "source": "whatsapp",
        "score": 74.0,
        "tier": "hot",
        "status": "proposal_sent",
        "assigned_to": "Sara M.",
    },
    {
        "name": "Dr. Noura Al-Rasheed",
        "phone": "+965-6600-1003",
        "specialty": "Pediatrics",
        "clinic_size": "small",
        "tower_preference": "Clinic III",
        "budget_range": "800-1200 KD/mo",
        "timeline": "3_6_months",
        "source": "web_chat",
        "score": 52.0,
        "tier": "warm",
        "status": "follow_up",
        "assigned_to": None,
    },
    {
        "name": "Dr. Khalid Al-Mudhaf",
        "phone": "+965-6600-1004",
        "specialty": "Ophthalmology",
        "clinic_size": "medium",
        "tower_preference": "Clinic V",
        "budget_range": "1200-2000 KD/mo",
        "timeline": "1_3_months",
        "source": "email",
        "score": 45.0,
        "tier": "warm",
        "status": "nurture",
        "assigned_to": "Ahmed K.",
    },
    {
        "name": "Dr. Fatima Al-Azmi",
        "phone": "+965-6600-1005",
        "specialty": "General Practice",
        "clinic_size": "small",
        "tower_preference": None,
        "budget_range": None,
        "timeline": "just_exploring",
        "source": "web_chat",
        "score": 22.0,
        "tier": "cold",
        "status": "new",
        "assigned_to": None,
    },
]


def seed_leads(db):
    existing = db.query(Lead).count()
    if existing >= len(LEADS):
        print(f"  Leads: {existing} already exist, skipping.")
        return []

    lead_objs = []
    for i, l in enumerate(LEADS):
        lead = Lead(
            session_id=f"seed-session-lead-{i+1}",
            name=l["name"],
            phone=l["phone"],
            specialty=l["specialty"],
            clinic_size=l["clinic_size"],
            tower_preference=l.get("tower_preference"),
            budget_range=l.get("budget_range"),
            timeline=l.get("timeline"),
            source=l["source"],
            score=l["score"],
            tier=l["tier"],
            status=l["status"],
            assigned_to=l.get("assigned_to"),
            created_at=now - timedelta(days=i * 3 + 1),
        )
        db.add(lead)
        lead_objs.append(lead)
    db.flush()
    print(f"  Leads: inserted {len(lead_objs)}")
    return lead_objs


# ─────────────────────────────────────────────────────────────────────────────
# 3. TICKETS  (8 open tickets across towers and priorities)
# ─────────────────────────────────────────────────────────────────────────────

TICKETS = [
    {
        "tenant_name": "Gulf Medical Centre",
        "tower": "Clinic IV",
        "floor": "9",
        "clinic_number": "904",
        "category": "hvac",
        "description": "HVAC unit not cooling. Temperature in clinic has reached 31°C. Patients affected.",
        "priority": "P1",
        "status": "in_progress",
        "vendor_idx": 0,  # Gulf HVAC Solutions
        "hours_ago": 2,
    },
    {
        "tenant_name": "Al-Noor Dental",
        "tower": "Clinic VI Tower A",
        "floor": "5",
        "clinic_number": "502",
        "category": "medical_gas",
        "description": "Nitrous oxide supply line pressure drop in dental suite. Procedure scheduled in 2 hours.",
        "priority": "P1",
        "status": "dispatched",
        "vendor_idx": 3,  # Medline
        "hours_ago": 1,
    },
    {
        "tenant_name": "Bright Eyes Clinic",
        "tower": "Clinic V",
        "floor": "3",
        "clinic_number": "301",
        "category": "electrical",
        "description": "Circuit breaker tripping every 30 minutes in the procedure room. Lights going out mid-operation.",
        "priority": "P2",
        "status": "en_route",
        "vendor_idx": 1,  # Al-Noor Electrical
        "hours_ago": 5,
    },
    {
        "tenant_name": "Kidz Health Clinic",
        "tower": "Clinic III",
        "floor": "7",
        "clinic_number": "710",
        "category": "plumbing",
        "description": "Water leak from ceiling above reception area. Staining tiles and affecting electrical sockets below.",
        "priority": "P2",
        "status": "in_progress",
        "vendor_idx": 2,  # Gulf Plumb
        "hours_ago": 6,
    },
    {
        "tenant_name": "Al-Shifa General",
        "tower": "Clinic IV",
        "floor": "12",
        "clinic_number": "1205",
        "category": "lift",
        "description": "Passenger lift stuck between floors 11 and 12. No occupants but lift is out of service.",
        "priority": "P2",
        "status": "dispatched",
        "vendor_idx": 3,  # Medline
        "hours_ago": 3,
    },
    {
        "tenant_name": "Wellness Centre",
        "tower": "Clinic VI Tower B",
        "floor": "2",
        "clinic_number": "202",
        "category": "pest",
        "description": "Cockroach sighting in pantry area. Needs treatment before Thursday.",
        "priority": "P3",
        "status": "open",
        "vendor_idx": None,
        "hours_ago": 48,
    },
    {
        "tenant_name": "CardioPlus Clinic",
        "tower": "Medical Centre",
        "floor": "4",
        "clinic_number": "401",
        "category": "civil",
        "description": "Ceiling tiles cracked and one has fallen in waiting area. Safety hazard for patients.",
        "priority": "P3",
        "status": "open",
        "vendor_idx": 2,  # Gulf Plumb (civil)
        "hours_ago": 24,
    },
    {
        "tenant_name": "Derma Care",
        "tower": "Clinic III",
        "floor": "6",
        "clinic_number": "607",
        "category": "cleaning",
        "description": "Deep cleaning required after minor flooding incident on floor 6. Biohazard protocol needed.",
        "priority": "P3",
        "status": "open",
        "vendor_idx": 4,  # CleanPro
        "hours_ago": 12,
    },
]

SLA_HOURS = {"P1": 2, "P2": 8, "P3": 48}


def seed_tickets(db, vendor_objs):
    existing = db.query(Ticket).count()
    if existing >= len(TICKETS):
        print(f"  Tickets: {existing} already exist, skipping.")
        return []

    ticket_objs = []
    for i, t in enumerate(TICKETS):
        created = now - timedelta(hours=t["hours_ago"])
        sla_hours = SLA_HOURS[t["priority"]]
        sla_deadline = created + timedelta(hours=sla_hours)
        vendor_id = None
        if t["vendor_idx"] is not None and vendor_objs:
            vendor_id = vendor_objs[t["vendor_idx"]].id

        ticket = Ticket(
            ref=f"MX-{i+1:04d}",
            session_id=f"seed-session-ticket-{i+1}",
            tenant_name=t["tenant_name"],
            tower=t["tower"],
            floor=t["floor"],
            clinic_number=t.get("clinic_number"),
            category=t["category"],
            description=t["description"],
            priority=t["priority"],
            status=t["status"],
            vendor_id=vendor_id,
            sla_deadline=sla_deadline,
            created_at=created,
        )
        db.add(ticket)
        ticket_objs.append(ticket)
    db.flush()
    print(f"  Tickets: inserted {len(ticket_objs)}")
    return ticket_objs


# ─────────────────────────────────────────────────────────────────────────────
# 4. WORK ORDERS  (3 work orders: 1 pending approval, 2 in progress)
# ─────────────────────────────────────────────────────────────────────────────

WORK_ORDERS = [
    {
        "tenant_name": "Gulf Medical Centre",
        "tower": "Clinic IV",
        "floor": "9",
        "service_type": "digital_display",
        "specification": {"size": "55_inch", "cms_addon": True, "quantity": 2},
        "quote_amount": 615.0,
        "quote_breakdown": {
            "hardware_kd": 480.0,
            "installation_kd": 90.0,
            "cms_addon_kd": 60.0,
            "tower_access_fee_kd": 35.0,
        },
        "status": "pending_approval",
        "vendor_idx": 5,  # Swift Signage
        "days_ago": 1,
    },
    {
        "tenant_name": "Bright Eyes Clinic",
        "tower": "Clinic V",
        "floor": "3",
        "service_type": "signage",
        "specification": {"type": "door_sign", "quantity": 3, "bilingual": True},
        "quote_amount": 285.0,
        "quote_breakdown": {
            "design_kd": 120.0,
            "print_kd": 90.0,
            "install_kd": 75.0,
        },
        "status": "in_progress",
        "vendor_idx": 5,  # Swift Signage
        "days_ago": 4,
    },
    {
        "tenant_name": "CardioPlus Clinic",
        "tower": "Medical Centre",
        "floor": "4",
        "service_type": "cctv",
        "specification": {"cameras": 4, "nvr": True, "type": "indoor"},
        "quote_amount": 670.0,
        "quote_breakdown": {
            "per_camera_kd": 340.0,
            "nvr_kd": 180.0,
            "cabling_per_camera_kd": 100.0,
            "installation_kd": 50.0,
        },
        "status": "in_progress",
        "vendor_idx": 5,  # Swift Signage (closest match for installs)
        "days_ago": 7,
    },
]


def seed_work_orders(db, vendor_objs):
    existing = db.query(WorkOrder).count()
    if existing >= len(WORK_ORDERS):
        print(f"  Work orders: {existing} already exist, skipping.")
        return []

    wo_objs = []
    for i, wo in enumerate(WORK_ORDERS):
        created = now - timedelta(days=wo["days_ago"])
        vendor_id = None
        if wo["vendor_idx"] is not None and vendor_objs:
            vendor_id = vendor_objs[wo["vendor_idx"]].id

        work_order = WorkOrder(
            ref=f"WO-{i+1:04d}",
            session_id=f"seed-session-wo-{i+1}",
            tenant_name=wo["tenant_name"],
            tower=wo["tower"],
            floor=wo["floor"],
            service_type=wo["service_type"],
            specification=json.dumps(wo["specification"]),
            quote_amount=wo["quote_amount"],
            quote_breakdown=json.dumps(wo["quote_breakdown"]),
            status=wo["status"],
            vendor_id=vendor_id,
            created_at=created,
        )
        db.add(work_order)
        wo_objs.append(work_order)
    db.flush()
    print(f"  Work orders: inserted {len(wo_objs)}")
    return wo_objs


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("Seeding Mazaya FM database...")
    try:
        vendor_objs = seed_vendors(db)

        # If vendors were already in DB, fetch them for FK references
        if not vendor_objs:
            vendor_objs = db.query(Vendor).order_by(Vendor.id).all()

        seed_leads(db)
        seed_tickets(db, vendor_objs)
        seed_work_orders(db, vendor_objs)
        db.commit()
        print("Done. Database seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
