from app_production import app


def test_government_departments_endpoint():
    client = app.test_client()
    response = client.get('/api/government-forms/departments')
    assert response.status_code == 200
    payload = response.get_json()
    slugs = {item['slug'] for item in payload['departments']}
    assert 'aadhaar' in slugs
    assert 'passport' in slugs


def test_government_forms_filter_returns_expected_aadhaar_form():
    client = app.test_client()
    response = client.get('/api/government-forms/forms?department=aadhaar&query=child%20below%205')
    assert response.status_code == 200
    payload = response.get_json()
    ids = {item['id'] for item in payload['forms']}
    assert 'aadhaar-form-3' in ids


def test_government_forms_recommendation_endpoint():
    client = app.test_client()
    response = client.post('/api/government-forms/recommend', json={
        'query': 'Which PAN form should a foreign company use?'
    })
    assert response.status_code == 200
    payload = response.get_json()
    ids = [item['id'] for item in payload['matches']]
    assert 'pan-form-96' in ids


def test_official_redirect_uses_state_route_for_ration_card():
    client = app.test_client()
    response = client.get('/government-forms/official/ration-card-new?state=maharashtra')
    assert response.status_code == 302
    assert response.headers['Location'] == 'https://nfsa.gov.in/State/MH'
