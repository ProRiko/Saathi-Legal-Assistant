import requests
from app.core.config import GEMINI_API_KEY, GEMINI_MODEL


SYSTEM_PROMPT = (
    'You are Saathi AI legal assistant for Indian legal information. '
    'Provide general legal information, not legal advice.'
)


def call_gemini(messages: list[dict], max_tokens: int, temperature: float) -> str:
    if not GEMINI_API_KEY:
        return 'AI provider is not configured. Please set GEMINI_API_KEY.'

    context = '\n'.join(f"{m['role']}: {m['content']}" for m in messages)
    prompt = f"{SYSTEM_PROMPT}\n\n{context}"

    payload = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': temperature,
            'maxOutputTokens': max_tokens,
        },
    }

    response = requests.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}',
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    candidates = data.get('candidates', [])
    if not candidates:
        return 'No response from AI provider.'

    parts = candidates[0].get('content', {}).get('parts', [])
    return ''.join(part.get('text', '') for part in parts).strip()
