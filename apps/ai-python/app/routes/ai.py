from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from app.core.security import verify_internal_signature, SignatureError
from app.schemas.chat import ChatRequest
from app.schemas.analyze import AnalyzeRequest
from app.schemas.classify import ClassifyRequest
from app.services.chat_service import generate_chat_reply
from app.services.analyze_service import analyze_document
from app.services.classify_service import classify_text


ai_bp = Blueprint('ai', __name__)


@ai_bp.errorhandler(ValidationError)
def handle_validation_error(exc: ValidationError):
    return jsonify({'status': 'error', 'error': 'validation_error', 'details': exc.errors()}), 422


@ai_bp.post('/ai/chat')
def ai_chat():
    try:
        verify_internal_signature(request)
    except SignatureError as exc:
        return jsonify({'status': 'error', 'error': str(exc)}), 401

    payload = ChatRequest(**(request.get_json(silent=True) or {}))
    return jsonify(generate_chat_reply(payload))


@ai_bp.post('/ai/analyze')
def ai_analyze():
    try:
        verify_internal_signature(request)
    except SignatureError as exc:
        return jsonify({'status': 'error', 'error': str(exc)}), 401

    payload = AnalyzeRequest(**(request.get_json(silent=True) or {}))
    return jsonify(analyze_document(payload))


@ai_bp.post('/ai/classify')
def ai_classify():
    try:
        verify_internal_signature(request)
    except SignatureError as exc:
        return jsonify({'status': 'error', 'error': str(exc)}), 401

    payload = ClassifyRequest(**(request.get_json(silent=True) or {}))
    return jsonify(classify_text(payload))
