"""
Mock CRM API server for testing and development.

This module provides a lightweight FastAPI-based mock CRM system
that simulates real CRM operations for development and testing purposes.

Features:
- Lead creation and management
- Visit scheduling
- Lead status updates
- In-memory data storage
- RESTful API endpoints
- Automatic data backup to JSON files
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os

app = FastAPI(
    title='Mock CRM',
    description='Mock CRM API for testing bot service integration with auto-save',
    version='1.0.0'
)

def auto_save_data():
    """
    Automatically save current CRM data to JSON file after every operation.
    Handles datetime objects by converting them to ISO format strings.
    """
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Convert datetime objects to strings for JSON serialization
        leads_serializable = {}
        for lead_id, lead_data in LEADS.items():
            leads_serializable[lead_id] = {}
            for key, value in lead_data.items():
                if isinstance(value, datetime):
                    leads_serializable[lead_id][key] = value.isoformat() + "Z"
                else:
                    leads_serializable[lead_id][key] = value
        
        visits_serializable = {}
        for visit_id, visit_data in VISITS.items():
            visits_serializable[visit_id] = {}
            for key, value in visit_data.items():
                if isinstance(value, datetime):
                    visits_serializable[visit_id][key] = value.isoformat() + "Z"
                else:
                    visits_serializable[visit_id][key] = value
        
        # Prepare data for export
        export_data = {
            "summary": {
                "total_leads": len(LEADS),
                "total_visits": len(VISITS),
                "last_updated": datetime.utcnow().isoformat() + "Z"
            },
            "leads": leads_serializable,
            "visits": visits_serializable
        }
        
        # Always save to the same file (latest data)
        filename = "data/crm_data_latest.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Auto-saved data to {filename} - Leads: {len(LEADS)}, Visits: {len(VISITS)}")
        
    except Exception as e:
        print(f"❌ Auto-save failed: {e}")


class LeadCreate(BaseModel):
    """
    Model for creating new leads.
    
    Attributes:
        name (str): Full name of the lead
        phone (str): Phone number of the lead
        city (str): City where the lead is located
        source (Optional[str]): Lead source (e.g., 'Instagram', 'Facebook')
    """
    name: str = Field(..., description="Full name of the lead")
    phone: str = Field(..., description="Phone number of the lead")
    city: str = Field(..., description="City where the lead is located")
    source: Optional[str] = Field(None, description="Lead source")


class VisitCreate(BaseModel):
    """
    Model for scheduling visits.
    
    Attributes:
        lead_id (str): Unique identifier of the lead
        visit_time (datetime): Scheduled time for the visit
        notes (Optional[str]): Additional notes for the visit
    """
    lead_id: str = Field(..., description="Unique identifier of the lead")
    visit_time: datetime = Field(..., description="Scheduled time for the visit")
    notes: Optional[str] = Field(None, description="Additional notes for the visit")


class LeadStatusUpdate(BaseModel):
    """
    Model for updating lead status.
    
    Attributes:
        status (str): New status for the lead (must match valid pattern)
        notes (Optional[str]): Additional notes for the status update
    """
    status: str = Field(..., pattern='^(NEW|IN_PROGRESS|FOLLOW_UP|WON|LOST)$', description="New lead status")
    notes: Optional[str] = Field(None, description="Additional notes for the status update")


# In-memory storage for mock data
LEADS: Dict[str, Dict[str, Any]] = {}
VISITS: Dict[str, Dict[str, Any]] = {}


@app.get('/crm/data/export')
def export_all_data():
    """
    Export all CRM data for viewing and backup.
    
    Returns:
        Dict containing all leads and visits data with summary statistics
    """
    return {
        "summary": {
            "total_leads": len(LEADS),
            "total_visits": len(VISITS),
            "export_timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "leads": LEADS,
        "visits": VISITS
    }


@app.get('/crm/leads/all')
def get_all_leads():
    """
    Get all leads data.
    
    Returns:
        Dict containing all leads with count
    """
    return {
        "count": len(LEADS),
        "leads": LEADS
    }


@app.get('/crm/visits/all')
def get_all_visits():
    """
    Get all visits data.
    
    Returns:
        Dict containing all visits with count
    """
    return {
        "count": len(VISITS),
        "visits": VISITS
    }


@app.post('/crm/data/save')
def save_data_to_file():
    """
    Save current CRM data to JSON file.
    
    Returns:
        Success message with file path
    """
    import json
    import os
    from datetime import datetime
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/crm_backup_{timestamp}.json"
    
    # Prepare data for export
    export_data = {
        "export_info": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_leads": len(LEADS),
            "total_visits": len(VISITS)
        },
        "leads": LEADS,
        "visits": VISITS
    }
    
    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    return {
        "message": "Data saved successfully",
        "file_path": filename,
        "data_summary": export_data["export_info"]
    }


@app.post('/crm/leads')
def create_lead(payload: LeadCreate):
    """
    Create a new lead in the CRM system.
    
    Args:
        payload (LeadCreate): Lead creation data
        
    Returns:
        Dict containing lead_id and initial status
        
    Examples:
        POST /crm/leads
        {
            "name": "John Smith",
            "phone": "9876543210",
            "city": "Delhi",
            "source": "Instagram"
        }
    """
    lead_id = str(uuid4())
    LEADS[lead_id] = {**payload.dict(), 'lead_id': lead_id, 'status': 'NEW'}
    
    # Auto-save data after creating lead
    auto_save_data()
    
    return {'lead_id': lead_id, 'status': 'NEW'}


@app.post('/crm/visits')
def create_visit(payload: VisitCreate):
    """
    Schedule a visit for an existing lead.
    
    Args:
        payload (VisitCreate): Visit scheduling data
        
    Returns:
        Dict containing visit_id and status
        
    Raises:
        HTTPException: If the lead is not found
        
    Examples:
        POST /crm/visits
        {
            "lead_id": "123e4567-e89b-12d3",
            "visit_time": "2025-10-03T15:00:00",
            "notes": "Follow-up meeting"
        }
    """
    if payload.lead_id not in LEADS:
        raise HTTPException(status_code=404, detail='Lead not found')
    
    visit_id = str(uuid4())
    VISITS[visit_id] = {**payload.dict(), 'visit_id': visit_id, 'status': 'SCHEDULED'}
    
    # Auto-save data after creating visit
    auto_save_data()
    
    return {'visit_id': visit_id, 'status': 'SCHEDULED'}


@app.post('/crm/leads/{lead_id}/status')
def update_lead_status(lead_id: str, payload: LeadStatusUpdate):
    """
    Update the status of an existing lead.
    
    Args:
        lead_id (str): Unique identifier of the lead
        payload (LeadStatusUpdate): Status update data
        
    Returns:
        Dict containing lead_id and updated status
        
    Raises:
        HTTPException: If the lead is not found
        
    Examples:
        POST /crm/leads/123e4567-e89b-12d3/status
        {
            "status": "WON",
            "notes": "Deal closed successfully"
        }
    """
    if lead_id not in LEADS:
        raise HTTPException(status_code=404, detail='Lead not found')
    
    LEADS[lead_id]['status'] = payload.status
    if payload.notes:
        LEADS[lead_id]['notes'] = payload.notes
    
    # Auto-save data after updating lead status
    auto_save_data()
    
    return {'lead_id': lead_id, 'status': payload.status}
