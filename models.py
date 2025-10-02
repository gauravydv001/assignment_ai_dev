"""
Pydantic models for API request and response schemas.

This module defines the data models used for API communication,
including request validation and response serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class BotRequest(BaseModel):
    """
    Request model for bot interactions.
    
    Attributes:
        transcript (str): The text transcript to be processed
        metadata (Optional[Dict[str, Any]]): Additional metadata for the request
    """
    transcript: str = Field(..., description="Text transcript to be processed by the bot")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the request")


class BotResponse(BaseModel):
    """
    Response model for bot interactions.
    
    Attributes:
        intent (str): The classified intent from the transcript
        entities (Dict[str, Optional[str]]): Extracted entities from the transcript
        crm_call (Optional[Dict[str, Any]]): Details about the CRM API call made
        result (Optional[Dict[str, str]]): Result of the bot operation
    """
    intent: str = Field(..., description="Classified intent from the transcript")
    entities: Dict[str, Optional[str]] = Field(..., description="Extracted entities from the transcript")
    crm_call: Optional[Dict[str, Any]] = Field(None, description="Details about the CRM API call")
    result: Optional[Dict[str, str]] = Field(None, description="Result of the bot operation")


class ErrorResponse(BaseModel):
    """
    Error response model for failed requests.
    
    Attributes:
        intent (Optional[str]): The intent that was being processed when error occurred
        error (Dict[str, str]): Error details including type and message
    """
    intent: Optional[str] = Field(None, description="Intent being processed when error occurred")
    error: Dict[str, str] = Field(..., description="Error details with type and message")
