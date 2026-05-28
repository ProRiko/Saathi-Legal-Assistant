from app.schemas.chat import ChatRequest
from app.services.provider_router import route_chat


def detect_intent(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ['salary', 'employment', 'termination']):
        return 'employment_law'
    if any(token in lowered for token in ['rent', 'tenant', 'eviction']):
        return 'property_law'
    if any(token in lowered for token in ['consumer', 'refund', 'defective']):
        return 'consumer_law'
    return 'general_legal'


def generate_chat_reply(payload: ChatRequest) -> dict:
    normalized_messages = [m.model_dump() for m in payload.messages]
    latest_user_text = next((m.content for m in reversed(payload.messages) if m.role == 'user'), '')
    max_tokens = int(payload.options.get('max_tokens', 700)) if payload.options else 700
    temperature = float(payload.options.get('temperature', 0.4)) if payload.options else 0.4

    reply, provider, model = route_chat(normalized_messages, max_tokens=max_tokens, temperature=temperature)

    return {
        'reply': reply,
        'intent': detect_intent(latest_user_text),
        'provider': provider,
        'model': model,
        'guardrails': {
            'added_citation': 'Act' in reply,
            'high_risk_caution': False,
        },
        'metadata': {
            'language': payload.language,
        },
    }
