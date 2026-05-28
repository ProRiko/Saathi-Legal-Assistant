from app.schemas.analyze import AnalyzeRequest


def analyze_document(payload: AnalyzeRequest) -> dict:
    lines = [line.strip() for line in payload.document_text.split('\n') if line.strip()]
    summary = ' '.join(lines[:3])[:500] if lines else 'No readable content provided.'

    return {
        'summary': summary,
        'key_clauses': lines[:5],
        'risks': [
            'Manual legal verification required for enforceability.',
            'Jurisdiction and dispute clauses should be validated.',
        ],
        'suggestions': [
            'Confirm governing law and dispute resolution section.',
            'Ask counsel to verify penalty/termination clauses.',
        ],
        'lawyer_recommendation': 'Consult a licensed advocate before filing or signing.',
    }
