import hashlib
import hmac
import time
from flask import Request
from app.core.config import INTERNAL_KEY, INTERNAL_SECRET, SIGNATURE_MAX_SKEW_SECONDS


class SignatureError(Exception):
    pass


def verify_internal_signature(request: Request) -> None:
    request_key = request.headers.get('X-Internal-Key', '')
    timestamp = request.headers.get('X-Request-Timestamp', '')
    signature = request.headers.get('X-Internal-Signature', '')

    if not INTERNAL_KEY or not INTERNAL_SECRET:
        raise SignatureError('Internal signing secret not configured')

    if request_key != INTERNAL_KEY:
        raise SignatureError('Invalid internal key')

    if not timestamp.isdigit():
        raise SignatureError('Missing or invalid timestamp')

    now = int(time.time())
    if abs(now - int(timestamp)) > SIGNATURE_MAX_SKEW_SECONDS:
        raise SignatureError('Signature timestamp expired')

    body = request.get_data(as_text=True)
    digest = hmac.new(
        INTERNAL_SECRET.encode('utf-8'),
        f'{timestamp}.{body}'.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(digest, signature):
        raise SignatureError('Invalid signature')
