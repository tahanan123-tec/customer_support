from typing import Literal, Optional
from pydantic import BaseModel, Field

class TicketRequest(BaseModel):
    """
    Schema representing an incoming support ticket to be classified.
    """
    ticket_id: str = Field(
        ..., 
        description="Required unique identifier for the ticket.",
        examples=["TKT-10293"]
    )
    channel: Optional[Literal["app", "sms", "call_center", "merchant_portal"]] = Field(
        None,
        description="Communication channel through which the ticket was received."
    )
    locale: Optional[Literal["bn", "en", "mixed"]] = Field(
        None,
        description="Language locale of the incoming message."
    )
    message: str = Field(
        ...,
        description="The raw ticket message content to analyze."
    )


class TicketResponse(BaseModel):
    """
    Schema representing the final classification and routing response for a ticket.
    """
    ticket_id: str = Field(
        ...,
        description="Unique identifier of the evaluated ticket."
    )
    case_type: Literal[
        "wrong_transfer",
        "payment_failed",
        "refund_request",
        "phishing_or_social_engineering",
        "other"
    ] = Field(
        ...,
        description="Classified case type category."
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Assigned urgency/severity level."
    )
    department: Literal[
        "customer_support",
        "dispute_resolution",
        "payments_ops",
        "fraud_risk"
    ] = Field(
        ...,
        description="Recommended department for ticket handling."
    )
    agent_summary: str = Field(
        ...,
        description="Concise summary generated for agents/human review."
    )
    human_review_required: bool = Field(
        ...,
        description="Indicates if a human agent must review the ticket classification."
    )
    confidence: float = Field(
        ...,
        description="AI confidence score for the classification (between 0.0 and 1.0).",
        ge=0.0,
        le=1.0
    )


class StatsResponse(BaseModel):
    """
    Schema representing system performance and routing metrics.
    """
    total: int = Field(..., description="Total number of tickets received.")
    by_case_type: dict[str, int] = Field(..., description="Counts of tickets classified by case type.")
    by_severity: dict[str, int] = Field(..., description="Counts of tickets classified by severity.")
    human_review_count: int = Field(..., description="Number of tickets flagged for manual human review.")
    recent: list[dict] = Field(..., description="Log of the most recent classification results.")
