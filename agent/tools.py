"""
Agent tool schemas and handler implementations for Mazaya FM.
Each tool has:
  - A LangChain tool definition
  - A handler function (called when the tool is invoked)
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Literal

from sqlalchemy.orm import Session
from langchain_core.tools import tool as langchain_tool
from pydantic import BaseModel, Field

from config import settings
from models import Lead, Ticket, WorkOrder, Vendor, Briefing
from agent.scoring import calculate_lead_score

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic models for tool inputs (LangChain format)
# ---------------------------------------------------------------------------

class CreateLeadInput(BaseModel):
    """Input for creating a new lead."""
    session_id: Optional[str] = "unknown"
    name: str
    phone: str
    specialty: str
    clinic_size: Optional[str] = "unknown"  # Can be sqm number or "small"/"medium"/"large"
    tower_preference: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    source: Literal["web_chat", "whatsapp", "email", "hotline"] = "web_chat"

class ScoreLeadInput(BaseModel):
    """Input for scoring a lead."""
    lead_id: int
    specialty: Optional[str] = None
    tower_preference: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    clinic_size: Optional[str] = None

class CreateTicketInput(BaseModel):
    """Input for creating a maintenance ticket."""
    session_id: Optional[str] = "unknown"
    tenant_name: Optional[str] = None
    tower: str
    floor: str
    clinic_number: Optional[str] = None
    category: Literal["hvac", "electrical", "plumbing", "lift", "fire", "medical_gas", "civil", "cleaning", "pest", "other"]
    description: str

class DispatchVendorInput(BaseModel):
    """Input for dispatching a vendor."""
    job_id: int
    job_type: Literal["ticket", "work_order"]
    category: str
    tower: str
    priority: Optional[Literal["P1", "P2", "P3"]] = None

class GetQuoteInput(BaseModel):
    """Input for getting a service quote."""
    service_type: str
    specifications: dict
    tower: Optional[str] = "default"

class CreateWorkOrderInput(BaseModel):
    """Input for creating a work order."""
    session_id: Optional[str] = "unknown"
    tenant_name: Optional[str] = None
    tower: Optional[str] = None
    floor: Optional[str] = None
    service_type: str
    specification: Optional[dict] = None
    quote_amount: float
    quote_breakdown: Optional[dict] = None

class RegisterVendorInput(BaseModel):
    """Input for registering a vendor."""
    company_name: str
    categories: list[str]
    towers_covered: Optional[list[str]] = ["all"]
    contact_name: str
    phone: str
    email: Optional[str] = None
    trade_licence: Optional[str] = None

class GenerateBriefingInput(BaseModel):
    """Input for generating a briefing."""
    period: Literal["daily", "weekly"] = "daily"
    language: Literal["en", "ar"] = "en"

class GetDashboardStatsInput(BaseModel):
    """Input for getting dashboard stats."""
    tower_filter: Optional[str] = None

# ---------------------------------------------------------------------------
# LangChain tool definitions
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "create_lead",
        "description": "Create a new lead record after completing qualification. Call when all required fields are collected.",
        "input_schema": CreateLeadInput.model_json_schema(),
    },
    {
        "name": "score_lead",
        "description": "Calculate lead score 0-100 based on collected qualification data.",
        "input_schema": ScoreLeadInput.model_json_schema(),
    },
    {
        "name": "create_ticket",
        "description": "Create a maintenance ticket. Call when issue type, tower, and floor are confirmed.",
        "input_schema": CreateTicketInput.model_json_schema(),
    },
    {
        "name": "dispatch_vendor",
        "description": "Select and dispatch the best available vendor for a ticket or work order.",
        "input_schema": DispatchVendorInput.model_json_schema(),
    },
    {
        "name": "get_quote",
        "description": "Generate a service quote from the rate card based on service specifications.",
        "input_schema": GetQuoteInput.model_json_schema(),
    },
    {
        "name": "create_work_order",
        "description": "Create a facility service work order after quote acceptance.",
        "input_schema": CreateWorkOrderInput.model_json_schema(),
    },
    {
        "name": "register_vendor",
        "description": "Register a new vendor in the system after collecting all required information.",
        "input_schema": RegisterVendorInput.model_json_schema(),
    },
    {
        "name": "generate_briefing",
        "description": "Generate the daily management briefing from current operational data.",
        "input_schema": GenerateBriefingInput.model_json_schema(),
    },
    {
        "name": "get_dashboard_stats",
        "description": "Retrieve current operational KPIs for the dashboard.",
        "input_schema": GetDashboardStatsInput.model_json_schema(),
    },
]

# LangChain tools (for binding to model)
@langchain_tool(args_schema=CreateLeadInput)
def create_lead_tool(session_id: str, name: str, phone: str, specialty: str, 
                     clinic_size: str = "unknown", tower_preference: str = None,
                     budget_range: str = None, timeline: str = None, 
                     source: str = "web_chat") -> dict:
    """Create a new lead record after completing qualification."""
    return {"_placeholder": "handled by execute_tool"}

@langchain_tool(args_schema=ScoreLeadInput)
def score_lead_tool(lead_id: int, specialty: str = None, tower_preference: str = None,
                   budget_range: str = None, timeline: str = None, clinic_size: str = None) -> dict:
    """Calculate lead score 0-100 based on collected qualification data."""
    return {"_placeholder": "handled by execute_tool"}

@langchain_tool(args_schema=CreateTicketInput)
def create_ticket_tool(session_id: str, tower: str, floor: str, category: str,
                      description: str, tenant_name: str = None, clinic_number: str = None) -> dict:
    """Create a maintenance ticket."""
    return {"_placeholder": "handled by execute_tool"}

@langchain_tool(args_schema=DispatchVendorInput)
def dispatch_vendor_tool(job_id: int, job_type: str, category: str, tower: str, priority: str = None) -> dict:
    """Select and dispatch the best available vendor."""
    return {"_placeholder": "handled by execute_tool"}

@langchain_tool(args_schema=GetQuoteInput)
def get_quote_tool(service_type: str, specifications: dict, tower: str = "default") -> dict:
    """Generate a service quote from the rate card."""
    return {"_placeholder": "handled by execute_tool"}

@langchain_tool(args_schema=CreateWorkOrderInput)
def create_work_order_tool(session_id: str, service_type: str, quote_amount: float,
                          tenant_name: str = None, tower: str = None, floor: str = None,
                          specification: dict = None, quote_breakdown: dict = None) -> dict:
    """Create a facility service work order."""
    return {"_placeholder": "handled by execute_tool"}

@langchain_tool(args_schema=RegisterVendorInput)
def register_vendor_tool(company_name: str, categories: list, contact_name: str, phone: str,
                        towers_covered: list = None, email: str = None, trade_licence: str = None) -> dict:
    """Register a new vendor in the system."""
    return {"_placeholder": "handled by execute_tool"}

@langchain_tool(args_schema=GenerateBriefingInput)
def generate_briefing_tool(period: str = "daily", language: str = "en") -> dict:
    """Generate the daily management briefing."""
    return {"_placeholder": "handled by execute_tool"}

@langchain_tool(args_schema=GetDashboardStatsInput)
def get_dashboard_stats_tool(tower_filter: str = None) -> dict:
    """Retrieve current operational KPIs."""
    return {"_placeholder": "handled by execute_tool"}

LANGCHAIN_TOOLS = [
    create_lead_tool,
    score_lead_tool,
    create_ticket_tool,
    dispatch_vendor_tool,
    get_quote_tool,
    create_work_order_tool,
    register_vendor_tool,
    generate_briefing_tool,
    get_dashboard_stats_tool,
]


# ---------------------------------------------------------------------------
# Priority mapping
# ---------------------------------------------------------------------------

P1_CATEGORIES = {"hvac", "electrical", "lift", "fire", "medical_gas"}
P2_CATEGORIES = {"plumbing", "civil"}
P3_CATEGORIES = {"cleaning", "pest", "other"}


def _get_priority(category: str) -> str:
    cat = category.lower()
    if cat in P1_CATEGORIES:
        return "P1"
    if cat in P2_CATEGORIES:
        return "P2"
    return "P3"


def _sla_deadline(priority: str) -> datetime:
    now = datetime.now(timezone.utc)
    hours_map = {
        "P1": settings.p1_sla_hours,
        "P2": settings.p2_sla_hours,
        "P3": settings.p3_sla_hours,
    }
    return now + timedelta(hours=hours_map.get(priority, 48))


# ---------------------------------------------------------------------------
# Rate card loading
# ---------------------------------------------------------------------------

def _load_rate_card() -> dict:
    import os
    card_path = os.path.join(os.path.dirname(__file__), "..", "data", "rate_card.json")
    card_path = os.path.abspath(card_path)
    try:
        with open(card_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Could not load rate card: {e}")
        return {}


# ---------------------------------------------------------------------------
# Handler functions
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def _normalize_clinic_size(size_input: Optional[str]) -> str:
    """Convert numeric sqm to size category."""
    if not size_input or size_input in ["small", "medium", "large", "unknown"]:
        return size_input or "unknown"
    
    # Try to extract number from string like "100sqft", "200", "100 sqm"
    import re
    match = re.search(r'(\d+)', str(size_input))
    if match:
        sqm = int(match.group(1))
        # Convert sqft to sqm if needed (rough conversion)
        if 'sqft' in str(size_input).lower() or 'sq ft' in str(size_input).lower():
            sqm = int(sqm * 0.092903)  # sqft to sqm
        
        if sqm < 50:
            return "small"
        elif sqm < 100:
            return "medium"
        else:
            return "large"
    
    return "unknown"

def handle_create_lead(db: Session, inputs: dict) -> dict:
    """Create lead + immediately score it."""
    # Normalize clinic size
    clinic_size = _normalize_clinic_size(inputs.get("clinic_size"))
    
    lead = Lead(
        session_id=inputs.get("session_id"),
        name=inputs["name"],
        phone=inputs.get("phone"),
        specialty=inputs.get("specialty"),
        clinic_size=clinic_size,
        tower_preference=inputs.get("tower_preference"),
        budget_range=inputs.get("budget_range"),
        timeline=inputs.get("timeline"),
        source=inputs.get("source", "web_chat"),
        status="new",
    )
    db.add(lead)
    db.flush()  # get id without committing

    # Auto-score
    score_result = calculate_lead_score(
        specialty=lead.specialty,
        tower_preference=lead.tower_preference,
        budget_range=lead.budget_range,
        timeline=lead.timeline,
        clinic_size=lead.clinic_size,
    )
    lead.score = score_result["score"]
    lead.tier = score_result["tier"]
    db.commit()
    db.refresh(lead)

    return {
        "lead_id": lead.id,
        "score": lead.score,
        "tier": lead.tier,
        "status": lead.status,
    }


def handle_score_lead(db: Session, inputs: dict) -> dict:
    """Re-score an existing lead."""
    lead_id = inputs["lead_id"]
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return {"error": f"Lead {lead_id} not found"}

    score_result = calculate_lead_score(
        specialty=inputs.get("specialty") or lead.specialty,
        tower_preference=inputs.get("tower_preference") or lead.tower_preference,
        budget_range=inputs.get("budget_range") or lead.budget_range,
        timeline=inputs.get("timeline") or lead.timeline,
        clinic_size=inputs.get("clinic_size") or lead.clinic_size,
    )
    lead.score = score_result["score"]
    lead.tier = score_result["tier"]
    db.commit()

    return {
        "lead_id": lead.id,
        "score": lead.score,
        "tier": lead.tier,
        "breakdown": score_result["breakdown"],
    }


def handle_create_ticket(db: Session, inputs: dict) -> dict:
    """Create ticket with auto-priority and dispatch vendor."""
    category = inputs["category"].lower()
    priority = _get_priority(category)
    sla_deadline = _sla_deadline(priority)

    ticket = Ticket(
        session_id=inputs.get("session_id"),
        tenant_name=inputs.get("tenant_name"),
        tower=inputs.get("tower"),
        floor=inputs.get("floor"),
        clinic_number=inputs.get("clinic_number"),
        category=category,
        description=inputs["description"],
        priority=priority,
        sla_deadline=sla_deadline,
        status="open",
        ref="MX-TEMP",  # temporary — set after flush
    )
    db.add(ticket)
    db.flush()

    # Set ref based on id
    ticket.ref = f"MX-{ticket.id:04d}"
    db.flush()

    # Dispatch vendor
    dispatch_result = handle_dispatch_vendor(db, {
        "job_id": ticket.id,
        "job_type": "ticket",
        "category": category,
        "tower": inputs.get("tower", ""),
        "priority": priority,
    })

    db.commit()
    db.refresh(ticket)

    return {
        "ticket_id": ticket.id,
        "ref": ticket.ref,
        "priority": ticket.priority,
        "sla_deadline": sla_deadline.isoformat(),
        "status": ticket.status,
        "vendor_dispatched": dispatch_result.get("vendor_id"),
        "vendor_name": dispatch_result.get("company_name"),
    }


def handle_dispatch_vendor(db: Session, inputs: dict) -> dict:
    """Find best active vendor for category/tower and assign to ticket or work order."""
    job_id = inputs["job_id"]
    job_type = inputs["job_type"]
    category = inputs.get("category", "").lower()
    tower = inputs.get("tower", "").lower()

    # Query all active vendors
    vendors = db.query(Vendor).filter(Vendor.status == "active").all()

    best_vendor = None
    best_score = -1

    for vendor in vendors:
        # Parse JSON fields
        try:
            vendor_categories = json.loads(vendor.categories or "[]")
        except (json.JSONDecodeError, TypeError):
            vendor_categories = []
        try:
            vendor_towers = json.loads(vendor.towers_covered or "[]")
        except (json.JSONDecodeError, TypeError):
            vendor_towers = []

        # Normalise for comparison
        vendor_cats_lower = [c.lower() for c in vendor_categories]
        vendor_towers_lower = [t.lower() for t in vendor_towers]

        # Category match
        category_match = (
            category in vendor_cats_lower
            or "all" in vendor_cats_lower
        )
        # Tower match
        tower_match = (
            not tower
            or tower in vendor_towers_lower
            or "all" in vendor_towers_lower
        )

        if category_match and tower_match and vendor.score > best_score:
            best_score = vendor.score
            best_vendor = vendor

    if not best_vendor:
        logger.warning(f"No vendor found for category={category} tower={tower}")
        return {"vendor_id": None, "message": "No suitable vendor found"}

    # Assign to ticket or work order
    if job_type == "ticket":
        job = db.query(Ticket).filter(Ticket.id == job_id).first()
        if job:
            job.vendor_id = best_vendor.id
            job.status = "dispatched"
    elif job_type == "work_order":
        job = db.query(WorkOrder).filter(WorkOrder.id == job_id).first()
        if job:
            job.vendor_id = best_vendor.id
            if job.status == "approved":
                job.status = "in_progress"

    # Don't commit here — caller commits
    return {
        "vendor_id": best_vendor.id,
        "company_name": best_vendor.company_name,
        "score": best_vendor.score,
        "contact_phone": best_vendor.phone,
    }


def handle_get_quote(db: Session, inputs: dict) -> dict:
    """Calculate quote from rate card."""
    service_type = inputs.get("service_type", "").lower().replace(" ", "_").replace("-", "_")
    specifications = inputs.get("specifications", {})
    tower = inputs.get("tower", "default")

    rate_card = _load_rate_card()
    services = rate_card.get("services", {})

    # Get surcharge
    tower_key = tower.lower().replace(" ", "_") if tower else "default"
    surcharges = rate_card.get("tower_access_surcharge", {})
    surcharge = surcharges.get(tower_key, surcharges.get("default", 1.0))

    total = 0.0
    breakdown = {}
    matched_service = None

    # Try to match service_type to rate card keys
    for key in services:
        if key in service_type or service_type in key:
            matched_service = key
            break

    if not matched_service:
        # Return a generic estimate
        return {
            "service_type": service_type,
            "total_kd": 0,
            "breakdown": {},
            "note": f"Service type '{service_type}' not in rate card. Please provide custom quote.",
        }

    service_rates = services[matched_service]

    # Calculate based on service type
    if matched_service == "digital_display":
        size = specifications.get("size", "43_inch")
        size_key = size.replace(" ", "_").replace('"', "_inch")
        size_rates = service_rates.get(size_key, service_rates.get("43_inch", {}))
        hardware = size_rates.get("hardware_kd", 0)
        installation = size_rates.get("installation_kd", 0)
        cms = service_rates.get("cms_addon_kd", 0) if specifications.get("cms", False) else 0
        access_fee = service_rates.get("tower_access_fee_kd", 0)
        qty = specifications.get("quantity", 1)
        total = (hardware + installation) * qty + cms + access_fee
        breakdown = {
            "hardware": hardware * qty,
            "installation": installation * qty,
            "cms_addon": cms,
            "tower_access_fee": access_fee,
        }

    elif matched_service == "signage":
        sign_type = specifications.get("type", "door_sign").replace(" ", "_")
        sign_rates = service_rates.get(sign_type, service_rates.get("door_sign", {}))
        qty = specifications.get("quantity", 1)
        item_total = sum(sign_rates.values()) * qty
        total = item_total
        breakdown = {k: v * qty for k, v in sign_rates.items()}

    elif matched_service == "cctv":
        cameras = specifications.get("cameras", 1)
        include_nvr = specifications.get("nvr", True)
        total = (
            service_rates["per_camera_kd"] * cameras
            + (service_rates["nvr_kd"] if include_nvr else 0)
            + service_rates["cabling_per_camera_kd"] * cameras
            + service_rates["installation_kd"]
        )
        breakdown = {
            "cameras": service_rates["per_camera_kd"] * cameras,
            "nvr": service_rates["nvr_kd"] if include_nvr else 0,
            "cabling": service_rates["cabling_per_camera_kd"] * cameras,
            "installation": service_rates["installation_kd"],
        }

    elif matched_service == "lighting":
        fixtures = specifications.get("fixtures", 1)
        total = (
            service_rates["per_fixture_kd"] * fixtures
            + service_rates["wiring_kd"]
            + service_rates["design_kd"]
        )
        breakdown = {
            "fixtures": service_rates["per_fixture_kd"] * fixtures,
            "wiring": service_rates["wiring_kd"],
            "design": service_rates["design_kd"],
        }

    elif matched_service == "partition":
        sqm = specifications.get("sqm", 10)
        doors = specifications.get("doors", 0)
        total = (
            service_rates["per_sqm_kd"] * sqm
            + service_rates["door_kd"] * doors
            + service_rates["finishing_kd"]
        )
        breakdown = {
            "partition_area": service_rates["per_sqm_kd"] * sqm,
            "doors": service_rates["door_kd"] * doors,
            "finishing": service_rates["finishing_kd"],
        }

    elif matched_service == "cleaning":
        sqm = specifications.get("sqm", 50)
        clean_type = specifications.get("type", "regular")
        if clean_type == "deep":
            total = service_rates["deep_clean_per_sqm_kd"] * sqm
            breakdown = {"deep_clean": total}
        elif clean_type == "carpet":
            total = service_rates["carpet_per_sqm_kd"] * sqm
            breakdown = {"carpet_clean": total}
        else:
            visits = specifications.get("visits", 1)
            total = service_rates["regular_per_visit_kd"] * visits
            breakdown = {"regular_visits": total}

    elif matched_service == "painting":
        sqm = specifications.get("sqm", 50)
        finish = specifications.get("finish", "standard")
        if finish == "specialty":
            rate = service_rates["specialty_finish_per_sqm_kd"]
        else:
            rate = service_rates["per_sqm_kd"] + service_rates["primer_per_sqm_kd"]
        total = rate * sqm
        breakdown = {"painting": total}

    elif matched_service == "flooring":
        sqm = specifications.get("sqm", 50)
        floor_type = specifications.get("floor_type", "vinyl")
        rate_key = f"{floor_type}_per_sqm_kd"
        rate = service_rates.get(rate_key, service_rates["vinyl_per_sqm_kd"])
        removal = service_rates["removal_per_sqm_kd"] * sqm if specifications.get("remove_existing", False) else 0
        total = rate * sqm + removal
        breakdown = {
            "flooring": rate * sqm,
            "removal": removal,
        }

    else:
        # Fallback: sum all numeric values in the service rates
        for k, v in service_rates.items():
            if isinstance(v, (int, float)):
                total += v
                breakdown[k] = v

    # Apply surcharge
    total = round(total * surcharge, 2)
    breakdown = {k: round(v * surcharge, 2) for k, v in breakdown.items()}

    return {
        "service_type": service_type,
        "total_kd": total,
        "breakdown": breakdown,
        "surcharge_applied": surcharge,
        "requires_approval": total > settings.auto_approval_threshold_kd,
    }


def handle_create_work_order(db: Session, inputs: dict) -> dict:
    """Create a work order, auto-approve if under threshold."""
    quote_amount = inputs.get("quote_amount", 0)
    auto_approve = quote_amount <= settings.auto_approval_threshold_kd

    wo = WorkOrder(
        session_id=inputs.get("session_id"),
        tenant_name=inputs.get("tenant_name"),
        tower=inputs.get("tower"),
        floor=inputs.get("floor"),
        service_type=inputs["service_type"],
        specification=json.dumps(inputs.get("specification") or {}),
        quote_amount=quote_amount,
        quote_breakdown=json.dumps(inputs.get("quote_breakdown") or {}),
        status="pending_approval",
        ref="WO-TEMP",
    )
    db.add(wo)
    db.flush()

    wo.ref = f"WO-{wo.id:04d}"
    db.flush()

    dispatch_result = {}
    if auto_approve:
        wo.status = "approved"
        wo.approved_by = "auto"
        # Dispatch vendor for approved work orders
        dispatch_result = handle_dispatch_vendor(db, {
            "job_id": wo.id,
            "job_type": "work_order",
            "category": inputs["service_type"].lower(),
            "tower": inputs.get("tower", ""),
        })

    db.commit()
    db.refresh(wo)

    return {
        "work_order_id": wo.id,
        "ref": wo.ref,
        "status": wo.status,
        "quote_amount_kd": quote_amount,
        "auto_approved": auto_approve,
        "vendor_dispatched": dispatch_result.get("vendor_id"),
        "vendor_name": dispatch_result.get("company_name"),
    }


def handle_register_vendor(db: Session, inputs: dict) -> dict:
    """Register a new vendor."""
    vendor = Vendor(
        company_name=inputs["company_name"],
        categories=json.dumps(inputs.get("categories", [])),
        towers_covered=json.dumps(inputs.get("towers_covered", ["all"])),
        contact_name=inputs.get("contact_name"),
        phone=inputs.get("phone"),
        email=inputs.get("email"),
        trade_licence=inputs.get("trade_licence"),
        status="onboarding",
        score=80.0,
        jobs_completed=0,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    return {
        "vendor_id": vendor.id,
        "company_name": vendor.company_name,
        "status": vendor.status,
        "message": "Vendor registered successfully. Status: onboarding. Our team will review and activate your account.",
    }


def handle_generate_briefing(db: Session, inputs: dict) -> dict:
    """Gather stats and generate a briefing, falling back to DB-only text."""
    from agent.prompts import BRIEFING_PROMPT_TEMPLATE
    from agent.llm import get_chat_model

    period = inputs.get("period", "daily")
    language = inputs.get("language", "en")

    # Gather stats
    stats = _gather_briefing_stats(db)

    # Build prompt
    language_name = "English" if language == "en" else "Arabic"
    prompt = BRIEFING_PROMPT_TEMPLATE.format(
        stats_json=json.dumps(stats, indent=2),
        language=language,
        language_name=language_name,
    )

    alerts = _generate_alerts(db, stats)
    briefing_text = ""
    model = None
    try:
        model = get_chat_model()
        response = model.invoke(prompt)
        briefing_text = _message_content_to_text(response)
        if not briefing_text.strip():
            raise ValueError("Groq returned an empty briefing")
    except Exception as e:
        logger.error(f"Briefing generation failed: {e}")
        briefing_text = _fallback_briefing_text(stats, alerts, period)

    # Generate Arabic if needed
    briefing_en = briefing_text if language == "en" else ""
    briefing_ar = briefing_text if language == "ar" else ""

    if language == "en" and settings.groq_api_key and model:
        # Also generate Arabic version
        try:
            ar_prompt = BRIEFING_PROMPT_TEMPLATE.format(
                stats_json=json.dumps(stats, indent=2),
                language="ar",
                language_name="Arabic",
            )
            ar_response = model.invoke(ar_prompt)
            briefing_ar = _message_content_to_text(ar_response)
        except Exception as e:
            logger.warning(f"Arabic briefing generation failed: {e}")
            briefing_ar = ""

    now = datetime.now(timezone.utc)
    briefing = Briefing(
        period=period,
        generated_at=now,
        briefing_en=briefing_en,
        briefing_ar=briefing_ar,
        alerts=json.dumps(alerts),
    )
    db.add(briefing)
    db.commit()
    db.refresh(briefing)

    return {
        "briefing_id": briefing.id,
        "period": period,
        "generated_at": now.isoformat(),
        "briefing_en": briefing_en,
        "briefing_ar": briefing_ar,
        "alerts_count": len(alerts),
    }


def _message_content_to_text(response: Any) -> str:
    """Convert LangChain message content variants into DB-safe text."""
    content = response.content if hasattr(response, "content") else response

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)

    return str(content or "")


def _fallback_briefing_text(stats: dict, alerts: list[dict], period: str) -> str:
    """Build a deterministic briefing when the LLM provider is unavailable."""
    priority_counts = stats.get("tickets_by_priority") or {}
    tier_counts = stats.get("leads_by_score_tier") or {}
    critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
    warning_alerts = [a for a in alerts if a.get("severity") == "warning"]
    top_towers = stats.get("tickets_by_tower") or []
    busiest_tower = max(top_towers, key=lambda row: row.get("count", 0), default=None)

    lines = [
        f"{period.title()} Operations Briefing",
        "",
        "Overall status:",
        f"- Open maintenance tickets: {stats.get('open_tickets', 0)}",
        f"- SLA compliance: {stats.get('sla_compliance_pct', 0)}%",
        f"- Active vendors: {stats.get('active_vendors', 0)}",
        f"- Chat sessions today: {stats.get('chat_sessions_today', 0)}",
        "",
        "Maintenance and work orders:",
        f"- Priority mix: P1 {priority_counts.get('P1', 0)}, P2 {priority_counts.get('P2', 0)}, P3 {priority_counts.get('P3', 0)}",
        f"- Pending work order approvals: {stats.get('pending_work_order_approvals', 0)}",
        f"- Completed work orders in 7 days: {stats.get('completed_work_orders_7d', 0)}",
        f"- 7-day work order revenue: KD {stats.get('revenue_7d_kd', 0)}",
        "",
        "Lead pipeline and vendors:",
        f"- Active lead pipeline: {stats.get('lead_pipeline_count', 0)}",
        f"- Lead tiers: hot {tier_counts.get('hot', 0)}, warm {tier_counts.get('warm', 0)}, cold {tier_counts.get('cold', 0)}",
        f"- Average active vendor score: {stats.get('avg_vendor_score', 0)}",
        f"- Vendors below threshold: {stats.get('vendors_below_threshold', 0)}",
    ]

    if busiest_tower:
        lines.append(f"- Busiest tower for open tickets: {busiest_tower.get('tower')} ({busiest_tower.get('count', 0)} tickets)")

    lines.extend([
        "",
        "Alerts requiring attention:",
        f"- Critical alerts: {len(critical_alerts)}",
        f"- Warnings: {len(warning_alerts)}",
    ])

    if alerts:
        for alert in alerts[:3]:
            lines.append(f"- {alert.get('message', 'Review operational alert')}")
    else:
        lines.append("- No active alerts at this time.")

    lines.extend([
        "",
        "Recommended priority actions:",
        "- Review breached P1 tickets and reassign vendors where needed.",
        "- Clear pending work order approvals to avoid service delays.",
        "- Assign hot leads that have not received follow-up.",
    ])

    return "\n".join(lines)


def handle_get_dashboard_stats(db: Session, inputs: dict) -> dict:
    """Aggregate DB stats for the dashboard."""
    return _gather_briefing_stats(db, tower_filter=inputs.get("tower_filter"))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _gather_briefing_stats(db: Session, tower_filter: Optional[str] = None) -> dict:
    """Aggregate operational stats from DB."""
    from sqlalchemy import func as sql_func
    from datetime import date

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Tickets
    ticket_q = db.query(Ticket)
    if tower_filter:
        ticket_q = ticket_q.filter(Ticket.tower.ilike(f"%{tower_filter}%"))

    open_tickets = ticket_q.filter(Ticket.status.notin_(["completed", "closed"])).count()
    tickets_by_priority = {
        "P1": ticket_q.filter(Ticket.priority == "P1", Ticket.status.notin_(["completed", "closed"])).count(),
        "P2": ticket_q.filter(Ticket.priority == "P2", Ticket.status.notin_(["completed", "closed"])).count(),
        "P3": ticket_q.filter(Ticket.priority == "P3", Ticket.status.notin_(["completed", "closed"])).count(),
    }

    # Tickets by tower
    tower_rows = (
        db.query(Ticket.tower, sql_func.count(Ticket.id).label("count"))
        .filter(Ticket.status.notin_(["completed", "closed"]))
        .group_by(Ticket.tower)
        .all()
    )
    tickets_by_tower = [{"tower": r.tower or "Unknown", "count": r.count} for r in tower_rows]

    # Avg TAT for completed tickets
    completed = db.query(Ticket).filter(Ticket.status.in_(["completed", "closed"])).all()
    avg_tat = 0.0
    if completed:
        tats = []
        for t in completed:
            if t.created_at and t.updated_at:
                diff = (t.updated_at - t.created_at).total_seconds() / 3600
                tats.append(diff)
        avg_tat = round(sum(tats) / len(tats), 1) if tats else 0.0

    # SLA compliance
    total_tickets = db.query(Ticket).count()
    breached = 0
    if total_tickets > 0:
        now = datetime.now(timezone.utc)
        breached = db.query(Ticket).filter(
            Ticket.sla_deadline < now,
            Ticket.status.notin_(["completed", "closed"]),
        ).count()
    sla_compliance_pct = round(((total_tickets - breached) / total_tickets * 100) if total_tickets else 100, 1)

    # Leads
    lead_q = db.query(Lead)
    lead_pipeline_count = lead_q.filter(Lead.status.notin_(["closed_won", "closed_lost"])).count()
    leads_by_tier = {
        "hot": lead_q.filter(Lead.tier == "hot").count(),
        "warm": lead_q.filter(Lead.tier == "warm").count(),
        "cold": lead_q.filter(Lead.tier == "cold").count(),
    }

    # Work orders
    pending_approvals = db.query(WorkOrder).filter(WorkOrder.status == "pending_approval").count()
    completed_wo_7d = db.query(WorkOrder).filter(
        WorkOrder.status == "completed",
        WorkOrder.updated_at >= today_start - timedelta(days=7),
    ).count()

    # Revenue (7d completed work orders)
    revenue_result = db.query(sql_func.sum(WorkOrder.quote_amount)).filter(
        WorkOrder.status == "completed",
        WorkOrder.updated_at >= today_start - timedelta(days=7),
    ).scalar()
    revenue_7d = round(float(revenue_result or 0), 2)

    # Vendors
    active_vendors = db.query(Vendor).filter(Vendor.status == "active").count()
    avg_vendor_score_result = db.query(sql_func.avg(Vendor.score)).filter(Vendor.status == "active").scalar()
    avg_vendor_score = round(float(avg_vendor_score_result or 0), 1)
    below_threshold = db.query(Vendor).filter(Vendor.score < 60).count()

    # Chat sessions today
    from models import ChatSession
    chat_sessions_today = db.query(ChatSession).filter(
        ChatSession.created_at >= today_start
    ).count()

    return {
        "open_tickets": open_tickets,
        "avg_tat_hours": avg_tat,
        "lead_pipeline_count": lead_pipeline_count,
        "active_vendors": active_vendors,
        "avg_vendor_score": avg_vendor_score,
        "vendors_below_threshold": below_threshold,
        "chat_sessions_today": chat_sessions_today,
        "sla_compliance_pct": sla_compliance_pct,
        "tickets_by_tower": tickets_by_tower,
        "leads_by_score_tier": leads_by_tier,
        "tickets_by_priority": tickets_by_priority,
        "pending_work_order_approvals": pending_approvals,
        "completed_work_orders_7d": completed_wo_7d,
        "revenue_7d_kd": revenue_7d,
    }


def _generate_alerts(db: Session, stats: dict) -> list:
    """Generate structured alerts for the briefing."""
    alerts = []
    now = datetime.now(timezone.utc)

    # P1 tickets overdue
    p1_overdue = db.query(Ticket).filter(
        Ticket.priority == "P1",
        Ticket.sla_deadline < now,
        Ticket.status.notin_(["completed", "closed"]),
    ).all()
    for t in p1_overdue:
        alerts.append({
            "severity": "critical",
            "entity_type": "ticket",
            "entity_id": t.id,
            "message": f"P1 ticket {t.ref}: {t.category.upper()} issue at {t.tower} Floor {t.floor}. SLA BREACHED.",
            "action_label": "Reassign vendor",
            "action_endpoint": f"PATCH /api/tickets/{t.id}/vendor",
        })

    # Pending work orders
    if stats.get("pending_work_order_approvals", 0) > 0:
        pending_wos = db.query(WorkOrder).filter(WorkOrder.status == "pending_approval").all()
        for wo in pending_wos:
            alerts.append({
                "severity": "warning",
                "entity_type": "work_order",
                "entity_id": wo.id,
                "message": f"Work order {wo.ref} pending approval: {wo.service_type} — {wo.quote_amount} KD.",
                "action_label": "Approve quote",
                "action_endpoint": f"PATCH /api/work-orders/{wo.id}/approve",
            })

    # Vendors below threshold
    below_vendors = db.query(Vendor).filter(Vendor.score < 60, Vendor.status == "active").all()
    for v in below_vendors:
        alerts.append({
            "severity": "warning",
            "entity_type": "vendor",
            "entity_id": v.id,
            "message": f"Vendor '{v.company_name}' score is {v.score}/100 — below acceptable threshold.",
            "action_label": "Review vendor",
            "action_endpoint": f"PATCH /api/vendors/{v.id}/status",
        })

    # Hot leads needing follow-up (created > 24h ago, still 'new')
    hot_leads = db.query(Lead).filter(
        Lead.tier == "hot",
        Lead.status == "new",
        Lead.created_at < now - timedelta(hours=24),
    ).all()
    for lead in hot_leads:
        alerts.append({
            "severity": "warning",
            "entity_type": "lead",
            "entity_id": lead.id,
            "message": f"Hot lead '{lead.name}' ({lead.specialty}) has not been followed up in over 24 hours.",
            "action_label": "Assign lead",
            "action_endpoint": f"PATCH /api/leads/{lead.id}/assign",
        })

    return alerts


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

def execute_tool(db: Session, tool_name: str, tool_input: dict) -> Any:
    """Route tool call to the appropriate handler."""
    # Strip _tool suffix if present (LangChain adds this)
    clean_name = tool_name.replace("_tool", "")
    
    handlers = {
        "create_lead": handle_create_lead,
        "score_lead": handle_score_lead,
        "create_ticket": handle_create_ticket,
        "dispatch_vendor": handle_dispatch_vendor,
        "get_quote": handle_get_quote,
        "create_work_order": handle_create_work_order,
        "register_vendor": handle_register_vendor,
        "generate_briefing": handle_generate_briefing,
        "get_dashboard_stats": handle_get_dashboard_stats,
    }
    handler = handlers.get(clean_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name} (cleaned: {clean_name})"}
    try:
        return handler(db, tool_input)
    except Exception as e:
        logger.exception(f"Tool {tool_name} failed: {e}")
        return {"error": str(e)}
