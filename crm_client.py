"""
CRM Client module for making HTTP requests to the CRM API.

This module provides a robust HTTP client with retry logic, timeouts,
and error handling for communicating with the CRM system.

Features:
- Automatic retries on server errors (500-504)
- Configurable timeouts
- Session-based connection pooling
- Structured error handling
"""

import requests
from requests.adapters import HTTPAdapter, Retry
from requests.models import Response
from typing import Optional
from settings import settings

# Configure session with retry strategy
session = requests.Session()
retries = Retry(
    total=2, 
    backoff_factor=1, 
    status_forcelist=[500, 502, 503, 504]
)
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

# Request timeout in seconds
TIMEOUT = 3


def create_lead(name: str, phone: str, city: str, source: Optional[str] = None) -> Response:
    """
    Create a new lead in the CRM system.
    
    Args:
        name (str): Full name of the lead
        phone (str): Phone number of the lead
        city (str): City where the lead is located
        source (Optional[str]): Lead source (e.g., 'Instagram', 'Facebook')
        
    Returns:
        Response: HTTP response object from the CRM API
        
    Raises:
        requests.exceptions.RequestException: If the request fails
        requests.exceptions.Timeout: If the request times out
        
    Examples:
        >>> response = create_lead("John Smith", "9876543210", "Delhi", "Instagram")
        >>> if response.status_code == 201:
        ...     lead_data = response.json()
        ...     print(f"Lead created with ID: {lead_data['lead_id']}")
    """
    url = f"{settings.CRM_BASE_URL.rstrip('/')}/crm/leads"
    payload = {"name": name, "phone": phone, "city": city}
    if source:
        payload['source'] = source
    
    resp = session.post(url, json=payload, timeout=TIMEOUT)
    return resp


def schedule_visit(lead_id: str, visit_time: str, notes: Optional[str] = None) -> Response:
    """
    Schedule a visit for an existing lead.
    
    Args:
        lead_id (str): Unique identifier of the lead
        visit_time (str): ISO format datetime string for the visit
        notes (Optional[str]): Additional notes for the visit
        
    Returns:
        Response: HTTP response object from the CRM API
        
    Raises:
        requests.exceptions.RequestException: If the request fails
        requests.exceptions.Timeout: If the request times out
        
    Examples:
        >>> response = schedule_visit("123e4567-e89b-12d3", "2025-10-03T15:00:00", "Follow-up call")
        >>> if response.status_code == 201:
        ...     visit_data = response.json()
        ...     print(f"Visit scheduled with ID: {visit_data['visit_id']}")
    """
    url = f"{settings.CRM_BASE_URL.rstrip('/')}/crm/visits"
    payload = {"lead_id": lead_id, "visit_time": visit_time}
    if notes:
        payload['notes'] = notes
    
    resp = session.post(url, json=payload, timeout=TIMEOUT)
    return resp


def update_lead_status(lead_id: str, status: str, notes: Optional[str] = None) -> Response:
    """
    Update the status of an existing lead.
    
    Args:
        lead_id (str): Unique identifier of the lead
        status (str): New status for the lead (NEW, IN_PROGRESS, FOLLOW_UP, WON, LOST)
        notes (Optional[str]): Additional notes for the status update
        
    Returns:
        Response: HTTP response object from the CRM API
        
    Raises:
        requests.exceptions.RequestException: If the request fails
        requests.exceptions.Timeout: If the request times out
        
    Examples:
        >>> response = update_lead_status("123e4567-e89b-12d3", "WON", "Deal closed successfully")
        >>> if response.status_code == 200:
        ...     lead_data = response.json()
        ...     print(f"Lead status updated to: {lead_data['status']}")
    """
    url = f"{settings.CRM_BASE_URL.rstrip('/')}/crm/leads/{lead_id}/status"
    payload = {"status": status}
    if notes:
        payload['notes'] = notes
    
    resp = session.post(url, json=payload, timeout=TIMEOUT)
    return resp
