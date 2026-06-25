def sanitize_summary(summary: str) -> str:
    """
    Evaluates the agent summary for unsafe or sensitive keywords.
    If any sensitive words are found, flags a warning and replaces
    the summary with a safe default.

    Args:
        summary (str): The raw agent summary string.

    Returns:
        str: The sanitized or original summary string.
    """
    lower_summary = summary.lower()
    unsafe_keywords = ["pin", "otp", "password", "card number", "পিন", "ওটিপি"]
    
    if any(keyword in lower_summary for keyword in unsafe_keywords):
        print("SAFETY BLOCK: unsafe content detected in agent_summary")
        return "Customer reported a suspicious interaction. Flagged for immediate fraud review."
        
    return summary


async def check_content_safety(text: str) -> bool:
    """
    Asynchronous helper to verify if a piece of text is safe.

    Args:
        text (str): The text content to check.

    Returns:
        bool: True if safe (no modifications needed), False otherwise.
    """
    sanitized = sanitize_summary(text)
    return sanitized == text
