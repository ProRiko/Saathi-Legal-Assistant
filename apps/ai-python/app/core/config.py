import os

INTERNAL_KEY = os.getenv('INTERNAL_KEY', '')
INTERNAL_SECRET = os.getenv('INTERNAL_SECRET', '')
SIGNATURE_MAX_SKEW_SECONDS = int(os.getenv('SIGNATURE_MAX_SKEW_SECONDS', '60'))

MODEL_PROVIDER = (os.getenv('MODEL_PROVIDER') or 'claude').strip().lower()
ANTHROPIC_API_KEY = (os.getenv('ANTHROPIC_API_KEY') or '').strip()
CLAUDE_MODEL = (os.getenv('CLAUDE_MODEL') or 'claude-3-5-haiku-20241022').strip()
GEMINI_API_KEY = (os.getenv('GEMINI_API_KEY') or '').strip()
GEMINI_MODEL = (os.getenv('GEMINI_MODEL') or 'gemini-2.5-flash').strip()
