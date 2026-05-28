from app.schemas.classify import ClassifyRequest


def classify_text(payload: ClassifyRequest) -> dict:
    text = payload.text.lower()

    if any(token in text for token in ['salary', 'employment', 'termination']):
        return {'intent': 'employment_law', 'confidence': 0.9, 'labels': ['salary', 'employment']}
    if any(token in text for token in ['rent', 'tenant', 'landlord']):
        return {'intent': 'property_law', 'confidence': 0.9, 'labels': ['rent', 'tenant']}
    if any(token in text for token in ['consumer', 'refund', 'product']):
        return {'intent': 'consumer_law', 'confidence': 0.88, 'labels': ['consumer', 'refund']}

    return {'intent': 'general_legal', 'confidence': 0.7, 'labels': ['general']}
