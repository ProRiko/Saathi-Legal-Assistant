# Saathi V2 Inter-Service API Contract

## Laravel -> Python `/ai/chat`

Request JSON:
```json
{
  "request_id": "uuid",
  "user_ref": "42",
  "conversation_ref": "uuid",
  "language": "english",
  "messages": [
    { "role": "user", "content": "My salary is unpaid" }
  ],
  "options": { "max_tokens": 700, "temperature": 0.4 }
}
```

Response JSON:
```json
{
  "reply": "You can issue a demand notice...",
  "intent": "employment_law",
  "provider": "claude",
  "model": "claude-3-5-haiku-20241022",
  "guardrails": { "added_citation": true, "high_risk_caution": false },
  "metadata": { "language": "english" }
}
```

## Laravel -> Python `/ai/analyze`
Request JSON:
```json
{
  "request_id": "uuid",
  "document_text": "...",
  "analysis_type": "contract_risk"
}
```

Response JSON:
```json
{
  "summary": "...",
  "key_clauses": ["..."],
  "risks": ["..."],
  "suggestions": ["..."],
  "lawyer_recommendation": "..."
}
```

## Laravel -> Python `/ai/classify`
Request JSON:
```json
{
  "request_id": "uuid",
  "text": "Tenant is not paying rent"
}
```

Response JSON:
```json
{
  "intent": "property_law",
  "confidence": 0.92,
  "labels": ["rent", "tenant"]
}
```

## Security Headers
- `X-Internal-Key`
- `X-Request-Timestamp`
- `X-Internal-Signature` (HMAC SHA256 over `timestamp.body`)
