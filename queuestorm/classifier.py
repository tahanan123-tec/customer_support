import os
import json
from anthropic import AsyncAnthropic
from queuestorm.models import TicketResponse

SYSTEM_PROMPT = """You are a CRM ticket classifier for bKash, a digital mobile financial service in Bangladesh.
Customers write in English, Bangla, or mixed. Handle all three equally well.
Return ONLY a valid JSON object with no markdown or explanation.

Fields:
{
  "case_type": "wrong_transfer|payment_failed|refund_request|phishing_or_social_engineering|other",
  "severity": "low|medium|high|critical",
  "department": "customer_support|dispute_resolution|payments_ops|fraud_risk",
  "agent_summary": "1-2 neutral English sentences about the issue",
  "confidence": 0.0 to 1.0
}

Rules:
1. OTP/PIN/password requests → phishing_or_social_engineering, critical, fraud_risk
2. Money sent to wrong person → wrong_transfer, high, dispute_resolution
3. Failed transaction, balance deducted → payment_failed, high, payments_ops
4. Customer-initiated refund → refund_request, low, customer_support
5. App bugs, general queries → other, low, customer_support

NEVER include the words PIN, OTP, password, or card number in agent_summary."""


async def classify_ticket(message: str, locale: str = "en") -> dict:
    """
    Call the Anthropic API using AsyncAnthropic to analyze the support ticket text.
    Uses the exact system prompt rules to classify the ticket into a JSON structure.

    On failure, retries once. If still failing, returns a fallback dictionary.

    Args:
        message (str): The support ticket text message.
        locale (str): The language locale ("en", "bn", or "mixed").

    Returns:
        dict: Parsed classification result containing keys: 'case_type', 'severity',
              'department', 'agent_summary', and 'confidence'.
    """
    fallback = {
        "case_type": "other",
        "severity": "low",
        "department": "customer_support",
        "agent_summary": "Unable to classify ticket. Routed for manual review.",
        "confidence": 0.1
    }

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[WARNING] ANTHROPIC_API_KEY is not set in environment.")
        return fallback

    client = AsyncAnthropic(api_key=api_key)

    for attempt in range(2):
        try:
            response = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"Message: {message}\nLocale: {locale}"
                    }
                ]
            )
            content = response.content[0].text.strip()
            
            # Clean up potential markdown code fence markers if model wrapped JSON
            if content.startswith("```"):
                lines = content.splitlines()
                if len(lines) >= 2:
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].startswith("```"):
                        lines = lines[:-1]
                content = "\n".join(lines).strip()

            data = json.loads(content)
            
            # Verify required keys are present
            required_keys = ["case_type", "severity", "department", "agent_summary", "confidence"]
            if all(k in data for k in required_keys):
                return data
            else:
                raise ValueError("Missing required keys in JSON response")
                
        except Exception as e:
            print(f"[WARNING] AI classification attempt {attempt + 1} failed: {e}")
            if attempt == 1:
                return fallback


async def classify_ticket_with_ai(ticket_id: str, text: str, locale: str = "en") -> TicketResponse:
    """
    Wrapper that routes the ticket message through classify_ticket and constructs a TicketResponse.

    Args:
        ticket_id (str): The unique identifier for the ticket.
        text (str): The ticket message.
        locale (str): The locale code.

    Returns:
        TicketResponse: The Pydantic model response.
    """
    res = await classify_ticket(text, locale)
    # Assume human review is required if confidence is low (< 0.8) or safety/fraud triggers it
    human_review = res["confidence"] < 0.8 or res["case_type"] == "phishing_or_social_engineering"
    
    return TicketResponse(
        ticket_id=ticket_id,
        case_type=res["case_type"],
        severity=res["severity"],
        department=res["department"],
        agent_summary=res["agent_summary"],
        confidence=res["confidence"],
        human_review_required=human_review
    )
