import pytest
from nlu import parse_transcript
import crm_client
from unittest.mock import Mock, patch
from app import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_nlu_lead_create():
    t = 'Add a new lead: Rohan Sharma from Gurgaon, phone 9876543210, source Instagram.'
    parsed = parse_transcript(t)
    assert parsed['intent'] == 'LEAD_CREATE'
    assert parsed['entities']['phone'] is not None
    assert parsed['entities']['city'] is not None

def test_nlu_lead_create_without_source():
    t = 'Create new lead John Smith from Delhi phone 8765432109'
    parsed = parse_transcript(t)
    assert parsed['intent'] == 'LEAD_CREATE'
    assert parsed['entities']['name'] == 'John Smith'
    assert parsed['entities']['phone'] == '8765432109'
    assert parsed['entities']['city'] == 'Delhi'

@patch('crm_client.session.post')
def test_handle_lead_create(mock_post):
    mock_resp = Mock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {'lead_id':'1234','status':'NEW'}
    mock_post.return_value = mock_resp
    payload = {'transcript':'Add a new lead Rohan Sharma from Gurgaon phone 9876543210 source Instagram.'}
    r = client.post('/bot/handle', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['intent'] == 'LEAD_CREATE'
    assert data['result']['message'] == 'Lead created'

@patch('crm_client.session.post')
def test_handle_lead_create_validation_error(mock_post):
    payload = {'transcript':'Add a new lead without proper details'}
    r = client.post('/bot/handle', json=payload)
    assert r.status_code == 400
    data = r.json()
    assert data['detail']['type'] == 'VALIDATION_ERROR'
