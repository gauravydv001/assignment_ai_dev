"""
AI-powered NLU module using OpenAI for enhanced intent classification and entity extraction.
This module can handle complex input patterns, multiple requests, and provides confidence scores.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from settings import settings

logger = logging.getLogger(__name__)

class AINLUProcessor:
    """
    AI-powered Natural Language Understanding processor using OpenAI GPT models.
    
    This class handles:
    - Intent classification with confidence scores
    - Entity extraction from complex text
    - Multiple request handling in single input
    - Fallback to rule-based NLU when AI fails
    """
    
    def __init__(self):
        """Initialize the AI NLU processor with OpenAI client."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not provided. AI NLU will be disabled.")
            self.client = None
        else:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for OpenAI API."""
        return """You are an expert NLU system for a CRM bot that processes voice transcripts.

Your task is to analyze text and extract:
1. Intent classification 
2. Entity extraction
3. Confidence scores
4. Handle multiple requests in one input

SUPPORTED INTENTS:
- LEAD_CREATE: Creating new leads with name, phone, city, optional source
- VISIT_SCHEDULE: Scheduling visits with lead_id, visit_time, optional notes  
- LEAD_UPDATE: Updating lead status with lead_id, status, optional notes
- UNKNOWN: When intent cannot be determined

VALID STATUSES: NEW, IN_PROGRESS, FOLLOW_UP, WON, LOST
KNOWN SOURCES: instagram, facebook, linkedin, website, google, ads

RESPONSE FORMAT (JSON only):
{
  "requests": [
    {
      "intent": "INTENT_NAME",
      "confidence": 0.95,
      "entities": {
        "entity_name": "value"
      },
      "reasoning": "Brief explanation"
    }
  ],
  "multiple_requests": true/false
}

ENTITY EXTRACTION RULES:
- name: Full names (e.g., "John Smith")
- phone: Phone numbers (normalize to digits only)
- city: City names
- lead_id: UUID format lead identifiers
- visit_time: Parse dates/times to ISO format when possible
- status: One of the valid statuses
- source: One of the known sources
- notes: Additional text information

Handle variations, typos, and conversational language. Provide confidence scores (0.0-1.0).
"""

    def parse_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Parse transcript using AI NLU with fallback to rule-based approach.
        
        Args:
            transcript: The input text transcript to analyze
            
        Returns:
            Dictionary containing parsed intent, entities, and metadata
        """
        if not self.client or not settings.USE_AI_NLU:
            logger.info("Using rule-based NLU fallback")
            return self._fallback_to_rule_based(transcript)
        
        try:
            logger.info(f"Processing transcript with AI NLU: {transcript[:100]}...")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Analyze this transcript: {transcript}"}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            logger.debug(f"AI response: {content}")
            
            # Parse JSON response
            ai_result = json.loads(content)
            
            # Handle multiple requests
            if ai_result.get("multiple_requests", False) and len(ai_result.get("requests", [])) > 1:
                return self._handle_multiple_requests(ai_result["requests"])
            
            # Single request handling
            if ai_result.get("requests") and len(ai_result["requests"]) > 0:
                request = ai_result["requests"][0]
                return {
                    "intent": request.get("intent", "UNKNOWN"),
                    "entities": request.get("entities", {}),
                    "confidence": request.get("confidence", 0.5),
                    "reasoning": request.get("reasoning", ""),
                    "ai_enhanced": True
                }
            
            logger.warning("AI returned no valid requests, falling back to rule-based")
            return self._fallback_to_rule_based(transcript)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response JSON: {e}")
            return self._fallback_to_rule_based(transcript)
        except Exception as e:
            logger.error(f"AI NLU processing failed: {e}")
            return self._fallback_to_rule_based(transcript)
    
    def _handle_multiple_requests(self, requests: List[Dict]) -> Dict[str, Any]:
        """
        Handle multiple requests in a single input.
        For now, return the first valid request with highest confidence.
        
        Args:
            requests: List of parsed requests from AI
            
        Returns:
            Single request result with metadata about multiple requests
        """
        logger.info(f"Handling {len(requests)} multiple requests")
        
        # Sort by confidence and take the highest
        valid_requests = [r for r in requests if r.get("intent") != "UNKNOWN"]
        if not valid_requests:
            return {"intent": "UNKNOWN", "entities": {}, "ai_enhanced": True}
        
        best_request = max(valid_requests, key=lambda x: x.get("confidence", 0))
        
        return {
            "intent": best_request.get("intent", "UNKNOWN"),
            "entities": best_request.get("entities", {}),
            "confidence": best_request.get("confidence", 0.5),
            "reasoning": best_request.get("reasoning", ""),
            "ai_enhanced": True,
            "multiple_requests_detected": True,
            "total_requests": len(requests),
            "all_requests": requests
        }
    
    def _fallback_to_rule_based(self, transcript: str) -> Dict[str, Any]:
        """
        Fallback to the original rule-based NLU system.
        
        Args:
            transcript: The input text transcript
            
        Returns:
            Rule-based parsing result with fallback indicator
        """
        from nlu import parse_transcript
        result = parse_transcript(transcript)
        result["ai_enhanced"] = False
        result["fallback_reason"] = "AI NLU unavailable or failed"
        return result

# Global instance
ai_nlu = AINLUProcessor()