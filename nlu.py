"""
Rule-based Natural Language Understanding module for CRM bot operations.

This module provides intent classification and entity extraction using
regular expressions and keyword matching. It serves as a fallback when
AI-enhanced NLU is not available.

Supported intents:
- LEAD_CREATE: Create new leads with name, phone, city, and optional source
- VISIT_SCHEDULE: Schedule visits with lead_id, visit_time, and optional notes
- LEAD_UPDATE: Update lead status with lead_id, status, and optional notes
- UNKNOWN: Fallback when intent cannot be determined
"""

import re
import uuid
from datetime import datetime
import dateparser
from typing import Dict, Any

# ✅ Known lead sources (expandable)
KNOWN_SOURCES = {"instagram", "facebook", "linkedin", "website", "google", "ads"}

# ✅ Status values
VALID_STATUSES = {"NEW", "IN_PROGRESS", "FOLLOW_UP", "WON", "LOST"}


def parse_transcript(transcript: str) -> Dict[str, Any]:
    """
    Parse a text transcript to extract intent and entities using rule-based approach.
    
    This function analyzes the input text to:
    1. Classify the intent (LEAD_CREATE, VISIT_SCHEDULE, LEAD_UPDATE, or UNKNOWN)
    2. Extract relevant entities based on the identified intent
    3. Validate extracted entities against known patterns
    
    Args:
        transcript (str): The input text transcript to analyze
        
    Returns:
        Dict[str, Any]: Dictionary containing:
            - intent (str): The classified intent
            - entities (Dict): Extracted entities specific to the intent
            
    Examples:
        >>> parse_transcript("Add a new lead John Smith from Delhi phone 9876543210")
        {'intent': 'LEAD_CREATE', 'entities': {'name': 'John Smith', 'phone': '9876543210', 'city': 'Delhi'}}
        
        >>> parse_transcript("Schedule visit for lead abc-123 tomorrow 3 PM")
        {'intent': 'VISIT_SCHEDULE', 'entities': {'lead_id': 'abc-123', 'visit_time': '2025-10-03T15:00:00'}}
    """
    text = transcript.strip()
    lowered = text.lower()

    # ------------------------
    # 1. LEAD_CREATE
    # ------------------------
    if "lead" in lowered and any(w in lowered for w in ["add", "create", "register", "new"]):
        name_match = re.search(r"(?:name\s+)?([A-Z][a-z]+\s+[A-Z][a-z]+)", text)
        phone_match = re.search(r"(\+91[-\s]?)?\d{5}[-\s]?\d{5}", text)
        city_match = re.search(r"(?:city\s+|from\s+)([A-Za-z]+)", text)

        entities = {}

        if name_match:
            entities["name"] = name_match.group(1).strip()

        if phone_match:
            entities["phone"] = re.sub(r"\D", "", phone_match.group(0))

        if city_match:
            entities["city"] = city_match.group(1).strip()

        # Optional source (via, referral, source, through)
        source_match = re.search(r"(?:via|source|referral|through)\s+([A-Za-z]+)", text, re.IGNORECASE)
        if source_match:
            candidate = source_match.group(1).capitalize()
            if candidate.lower() in KNOWN_SOURCES:
                entities["source"] = candidate

        if {"name", "phone", "city"}.issubset(entities.keys()):
            return {"intent": "LEAD_CREATE", "entities": entities}

    # ------------------------
    # 2. VISIT_SCHEDULE
    # ------------------------
    if any(keyword in lowered for keyword in ["visit", "appointment", "meeting", "schedule"]):
        entities = {}
        
        # Look for lead ID - more flexible patterns (UUID format and short IDs)  
        lead_patterns = [
            r"lead\s+([0-9a-fA-F-]{8,})",  # Long UUID-style IDs
            r"lead\s+([a-zA-Z0-9-]{3,})",  # Short alphanumeric IDs (at least 3 chars)
        ]
        
        for pattern in lead_patterns:
            lead_match = re.search(pattern, text, re.IGNORECASE)
            if lead_match:
                lead_id = lead_match.group(1).strip()
                # Make sure we didn't capture keywords
                if lead_id.lower() not in ['at', 'on', 'for', 'with', 'and', 'or']:
                    entities["lead_id"] = lead_id
                    break

        # Look for time information - specific patterns to avoid capturing lead IDs
        time_patterns = [
            # ISO format datetime (e.g., "2025-10-03T15:00:00")
            r"(?:at|on)\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
            # Date with time (e.g., "2025-10-03 15:00", "October 3 3 PM")
            r"(?:at|on)\s+(\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2})",
            r"(?:at|on)\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s+\d{1,2}\s*(?:AM|PM)?)",
            # Relative dates with time (e.g., "tomorrow at 3 PM")
            r"(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)",
            # Just time (e.g., "at 3 PM", "at 15:00")
            r"(?:at|on)\s+(\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)",
            # Simple time without keywords
            r"(\d{1,2}:\d{2}(?:\s*(?:AM|PM))?)",
        ]
        
        time_text = None
        for pattern in time_patterns:
            time_match = re.search(pattern, text, re.IGNORECASE)
            if time_match:
                if len(time_match.groups()) > 1:
                    # Combine day and time
                    time_text = f"{time_match.group(1)} {time_match.group(2)}"
                else:
                    time_text = time_match.group(1).strip()
                break

        if time_text:
            parsed_time = dateparser.parse(time_text)
            if parsed_time:
                entities["visit_time"] = parsed_time.isoformat()

        # Look for notes - more flexible pattern
        notes_patterns = [
            r"notes?\s+(.+)$",  # "notes client meeting"
            r"notes?:\s*(.+)$",  # "notes: client meeting"
        ]
        
        for pattern in notes_patterns:
            notes_match = re.search(pattern, text, re.IGNORECASE)
            if notes_match:
                entities["notes"] = notes_match.group(1).strip()
                break

        if {"lead_id"}.issubset(entities.keys()) and ("visit_time" in entities or time_text):
            # If we have lead_id and some time indication, it's likely a visit schedule
            if "visit_time" not in entities and time_text:
                # Fallback: use the raw time text if parsing failed
                entities["visit_time"] = time_text
            return {"intent": "VISIT_SCHEDULE", "entities": entities}

    # ------------------------
    # 3. LEAD_UPDATE
    # ------------------------
    if "update" in lowered or "mark" in lowered or "status" in lowered:
        lead_match = re.search(r"lead\s+([0-9a-fA-F-]+)", text)
        status_match = re.search(r"(NEW|IN PROGRESS|FOLLOW UP|WON|LOST)", text, re.IGNORECASE)

        entities = {}

        if lead_match:
            entities["lead_id"] = lead_match.group(1).strip()

        if status_match:
            status = status_match.group(1).upper().replace(" ", "_")
            if status in VALID_STATUSES:
                entities["status"] = status

        notes_match = re.search(r"notes?:\s*(.+)", text, re.IGNORECASE)
        if notes_match:
            entities["notes"] = notes_match.group(1).strip()

        if {"lead_id", "status"}.issubset(entities.keys()):
            return {"intent": "LEAD_UPDATE", "entities": entities}

    # ------------------------
    # 4. UNKNOWN fallback
    # ------------------------
    return {"intent": "UNKNOWN", "entities": {}}



