from nlu import parse_transcript
from fastapi.testclient import TestClient
from app import app
from unittest.mock import Mock, patch

client = TestClient(app)

def test_nlu_visit_schedule():
    t = 'Schedule a visit for lead 7b1b8f54-aaaa-bbbb-cccc-1234567890ab at 2025-10-02T17:00:00+05:30'
    parsed = parse_transcript(t)
    assert parsed['intent'] == 'VISIT_SCHEDULE' or parsed['entities']['visit_time'] is not None

def test_nlu_visit_schedule_with_notes():
    t = 'Schedule visit for lead abc-123 at 2025-10-03T10:00:00 notes client meeting'
    parsed = parse_transcript(t)
    assert parsed['intent'] == 'VISIT_SCHEDULE'
    assert 'lead_id' in parsed['entities']
    assert 'visit_time' in parsed['entities']

@patch('crm_client.session.post')
def test_handle_visit_schedule(mock_post):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {'visit_id':'v-1','status':'SCHEDULED'}
    mock_post.return_value = mock_resp
    payload = {'transcript':'Schedule a visit for lead 7b1b8f54-aaaa-bbbb-cccc-1234567890ab at 2025-10-02T17:00:00+05:30'}
    r = client.post('/bot/handle', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['result']['message'] == 'Visit scheduled'

@patch('crm_client.session.post')
def test_handle_visit_schedule_validation_error(mock_post):
    payload = {'transcript':'Schedule visit without proper details'}
    r = client.post('/bot/handle', json=payload)
    assert r.status_code == 400
    data = r.json()
    assert data['detail']['type'] == 'VALIDATION_ERROR'
