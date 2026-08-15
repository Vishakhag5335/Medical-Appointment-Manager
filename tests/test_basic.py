import pytest
from app import create_app


@pytest.fixture
def client():
    """Test client fixture configured for testing environment."""
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_health_check(client):
    """Test the /health endpoint returns HTTP 200 and healthy status JSON."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'service' in data
    assert 'version' in data


def test_index_page(client):
    """Test the home page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'MedCare Manager' in response.data
