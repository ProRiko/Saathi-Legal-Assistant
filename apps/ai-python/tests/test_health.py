import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import create_app


def test_health_endpoint():
    app = create_app()
    client = app.test_client()
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json['status'] == 'healthy'
