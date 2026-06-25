import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from queuestorm.models import TicketRequest, TicketResponse, StatsResponse
from queuestorm.stats import Stats
from queuestorm.fast_path import fast_path_classify
from queuestorm.guard import sanitize_summary
from queuestorm.classifier import classify_ticket

# Initialize global stats tracker singleton
stats = Stats()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.
    Handles startup tasks like loading environment variables and verifying configurations.
    """
    # Load .env file at startup
    load_dotenv()
    
    # Verify environment variables
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[WARNING] ANTHROPIC_API_KEY is not set. AI-based classification will fail!")
    else:
        print("[INFO] ANTHROPIC_API_KEY loaded successfully.")

    print("[STARTUP] QueueStorm FastAPI CRM Ticket Classifier is starting up...")
    
    yield
    
    print("[SHUTDOWN] QueueStorm FastAPI CRM Ticket Classifier is shutting down...")


# Create FastAPI application instance
app = FastAPI(
    title="QueueStorm CRM Ticket Classifier",
    description="Production-ready asynchronous CRM support ticket routing and classification service.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS Middleware (allowing all origins for demo/testing purposes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/sort-ticket", response_model=TicketResponse)
async def sort_ticket(ticket: TicketRequest) -> TicketResponse:
    """
    FastAPI endpoint to classify and route an incoming support ticket.
    
    Orchestration logic:
    1. Call fast_path_classify(ticket.message)
    2. If result -> skip LLM, set fast_pathed=True
    3. Else -> call await classify_ticket(ticket.message, ticket.locale)
    4. Run sanitize_summary() on agent_summary
    5. Set human_review_required = True if severity=="critical" or case_type=="phishing_or_social_engineering"
    6. Call stats.record() with timestamp
    7. Return TicketResponse
    """
    res = fast_path_classify(ticket.message)
    fast_pathed = False
    
    if res:
        fast_pathed = True
    else:
        # If locale is None, default to "en"
        locale = ticket.locale or "en"
        res = await classify_ticket(ticket.message, locale)

    # Sanitize the summary to filter out sensitive credentials
    res["agent_summary"] = sanitize_summary(res["agent_summary"])

    # Determine if human review is required
    severity = res.get("severity")
    case_type = res.get("case_type")
    human_review = True if (severity == "critical" or case_type == "phishing_or_social_engineering") else False

    # Construct the final TicketResponse values
    response_data = {
        "ticket_id": ticket.ticket_id,
        "case_type": case_type,
        "severity": severity,
        "department": res.get("department"),
        "agent_summary": res.get("agent_summary"),
        "human_review_required": human_review,
        "confidence": res.get("confidence", 0.0)
    }

    # Record the metrics in stats singleton
    timestamp = datetime.now(timezone.utc).isoformat()
    stats.record(response_data, timestamp)

    return TicketResponse(**response_data)


@app.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """
    FastAPI endpoint to fetch the current in-memory performance and usage statistics.
    """
    return StatsResponse(**stats.summary())


@app.get("/tickets", response_model=List[Dict[str, Any]])
async def get_tickets() -> List[Dict[str, Any]]:
    """
    FastAPI endpoint to retrieve the list of recent tickets processed (up to 50).
    """
    return list(stats.recent)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    FastAPI endpoint for simple health and liveness checks.
    """
    return {
        "status": "ok",
        "service": "queuestorm"
    }
