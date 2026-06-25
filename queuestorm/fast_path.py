from typing import Optional
from queuestorm.models import TicketResponse

def fast_path_classify(message: str) -> dict | None:
    """
    Perform a rule-based keyword match classification on the ticket message.
    Converts the message to lowercase and checks patterns in order.

    Args:
        message (str): The support ticket message content to evaluate.

    Returns:
        dict | None: Dictionary containing 'case_type', 'severity', 'department',
                     'agent_summary', and 'confidence' if matched; otherwise None.
    """
    lower_message = message.lower()
    
    # 1. Phishing or Social Engineering check
    group1_a = ["otp", "pin", "password", "ওটিপি", "পিন"]
    group1_b = ["send", "share", "দাও", "দিন", "asked"]
    if any(k in lower_message for k in group1_a) and any(k in lower_message for k in group1_b):
        return {
            "case_type": "phishing_or_social_engineering",
            "severity": "critical",
            "department": "fraud_risk",
            "confidence": 0.97,
            "agent_summary": "Customer reported a suspicious request for account credentials. Flagged for immediate fraud review."
        }

    # 2. Wrong Transfer check
    group2 = ["wrong number", "wrong person", "ভুল নম্বর"]
    if any(k in lower_message for k in group2):
        return {
            "case_type": "wrong_transfer",
            "severity": "high",
            "department": "dispute_resolution",
            "confidence": 0.92,
            "agent_summary": "Customer reports sending money to an unintended recipient and requests recovery assistance."
        }

    # 3. Payment Failed check
    group3 = ["payment failed", "transaction failed", "পেমেন্ট হয়নি", "balance deducted"]
    if any(k in lower_message for k in group3):
        return {
            "case_type": "payment_failed",
            "severity": "high",
            "department": "payments_ops",
            "confidence": 0.90,
            "agent_summary": "Customer reports a failed transaction with possible balance deduction. Requires payment investigation."
        }

    return None


async def check_fast_path(ticket_id: str, text: str) -> Optional[TicketResponse]:
    """
    Asynchronous wrapper for fast_path_classify that constructs a TicketResponse.

    Args:
        ticket_id (str): The unique identifier of the ticket.
        text (str): The ticket message.

    Returns:
        Optional[TicketResponse]: A validated Pydantic model response if fast-pathed; otherwise None.
    """
    res = fast_path_classify(text)
    if res is None:
        return None
        
    return TicketResponse(
        ticket_id=ticket_id,
        case_type=res["case_type"],
        severity=res["severity"],
        department=res["department"],
        agent_summary=res["agent_summary"],
        confidence=res["confidence"],
        human_review_required=False
    )
