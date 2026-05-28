from app.core.config import MODEL_PROVIDER
from app.services.providers.claude_provider import call_claude
from app.services.providers.gemini_provider import call_gemini


def route_chat(messages: list[dict], max_tokens: int = 700, temperature: float = 0.4) -> tuple[str, str, str]:
    provider = MODEL_PROVIDER

    if provider == 'gemini':
        text = call_gemini(messages, max_tokens=max_tokens, temperature=temperature)
        return text, 'gemini', 'gemini-2.5-flash'

    text = call_claude(messages, max_tokens=max_tokens, temperature=temperature)
    return text, 'claude', 'claude-3-5-haiku-20241022'
