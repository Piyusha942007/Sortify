import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_demo_stats(client):
    res = client.get('/api/demo/stats')
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "composition" in data["data"]

def test_demo_emails(client):
    res = client.get('/api/demo/emails')
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["data"]) >= 60

def test_demo_rules(client):
    res = client.get('/api/demo/rules')
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["data"]) >= 5

def test_demo_unsub_queue(client):
    res = client.get('/api/demo/unsubscribe/queue')
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True

def test_demo_unsub_done(client):
    res = client.get('/api/demo/unsubscribe/done')
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True

def test_demo_log(client):
    res = client.get('/api/demo/log')
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["data"]) <= 15

def test_demo_plugins(client):
    res = client.get('/api/demo/plugins')
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["data"]) == 1

def test_demo_create_rule(client):
    res = client.post('/api/demo/rules', json={"label": "Shopping", "domain": "amazon.com"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["label"] == "Shopping"
    assert data["data"]["domain"] == "amazon.com"

def test_demo_unsub_approve(client):
    res = client.post('/api/demo/unsubscribe/approve', json={"sender_email": "hn-digest@hn.com"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["sender_email"] == "hn-digest@hn.com"
