from nlu import parse_transcript
from fastapi.testclient import TestClient
from app import app
from unittest.mock import Mock, patch

client = TestClient(app)

def test_nlu_lead_update():
    t = 'Update lead 7b1b8f54-aaaa-bbbb-cccc-1234567890ab to WON notes booked unit A2'
    parsed = parse_transcript(t)
    assert parsed['intent'] == 'LEAD_UPDATE' or parsed['entities']['status'] is not None

def test_nlu_lead_update_different_status():
    t = 'Mark lead abc-123-def-456 status IN PROGRESS'
    parsed = parse_transcript(t)
    assert parsed['intent'] == 'LEAD_UPDATE'
    assert 'lead_id' in parsed['entities']
    assert parsed['entities']['status'] == 'IN_PROGRESS'

@patch('crm_client.session.post')
def test_handle_lead_update(mock_post):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {'lead_id':'1234','status':'WON'}
    mock_post.return_value = mock_resp
    payload = {'transcript':'Update lead 7b1b8f54-aaaa-bbbb-cccc-1234567890ab to WON notes booked unit A2'}
    r = client.post('/bot/handle', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['result']['message'] == 'Lead status updated'

@patch('crm_client.session.post')
def test_handle_lead_update_validation_error(mock_post):
    payload = {'transcript':'Update lead without proper status'}
    r = client.post('/bot/handle', json=payload)
    assert r.status_code == 400
    data = r.json()
    assert data['detail']['type'] == 'VALIDATION_ERROR'
