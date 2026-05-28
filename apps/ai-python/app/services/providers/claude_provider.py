import requests
from app.core.config import ANTHROPIC_API_KEY, CLAUDE_MODEL


SYSTEM_PROMPT = (
    'You are Saathi AI legal assistant for Indian legal information. '
    'Provide general legal information, not legal advice.'
)


def call_claude(messages: list[dict], max_tokens: int, temperature: float) -> str:
    if not ANTHROPIC_API_KEY:
        return 'AI provider is not configured. Please set ANTHROPIC_API_KEY.'

    payload = {
        'model': CLAUDE_MODEL,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'system': SYSTEM_PROMPT,
        'messages': [
            {
                'role': m['role'],
                'content': [{'type': 'text', 'text': m['content']}],
            }
            for m in messages
            if m.get('role') in {'user', 'assistant'}
        ],
    }

    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return ''.join(part.get('text', '') for part in data.get('content', []) if part.get('type') == 'text').strip()
