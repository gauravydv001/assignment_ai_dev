"""
Logging configuration module for the AI Bot Service.
Provides structured logging with different levels and analytics tracking.
"""

import logging
import logging.config
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from pythonjsonlogger import jsonlogger
from settings import settings

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Analytics log file for JSONL format
ANALYTICS_LOG_FILE = LOGS_DIR / "analytics.jsonl"

class AnalyticsLogger:
    """
    Analytics logger for tracking bot interactions in JSONL format.
    
    Tracks:
    - Request timestamps and details
    - Intent classification results
    - Entity extraction success
    - CRM API call results
    - Response times and success rates
    """
    
    def __init__(self, log_file: str = str(ANALYTICS_LOG_FILE)):
        """
        Initialize analytics logger.
        
        Args:
            log_file: Path to the JSONL analytics log file
        """
        self.log_file = log_file
        self.logger = logging.getLogger("analytics")
    
    def log_interaction(
        self,
        request_id: str,
        transcript: str,
        intent: str,
        entities: Dict[str, Any],
        confidence: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        response_time_ms: Optional[float] = None,
        crm_call_result: Optional[Dict[str, Any]] = None,
        ai_enhanced: bool = False
    ):
        """
        Log a bot interaction to analytics file.
        
        Args:
            request_id: Unique identifier for the request
            transcript: Original user input
            intent: Classified intent
            entities: Extracted entities
            confidence: AI confidence score (if available)
            success: Whether the request was successful
            error_message: Error message if failed
            response_time_ms: Response time in milliseconds
            crm_call_result: CRM API call details
            ai_enhanced: Whether AI NLU was used
        """
        analytics_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id,
            "transcript": transcript,
            "transcript_length": len(transcript),
            "intent": intent,
            "entities": entities,
            "entity_count": len(entities),
            "confidence": confidence,
            "success": success,
            "error_message": error_message,
            "response_time_ms": response_time_ms,
            "crm_call_result": crm_call_result,
            "ai_enhanced": ai_enhanced
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(analytics_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write analytics log: {e}")

def setup_logging():
    """
    Set up comprehensive logging configuration for the application.
    
    Creates multiple loggers:
    - Application logger (structured JSON)
    - Analytics logger (JSONL format)
    - Error logger (separate file)
    """
    
    # Logging configuration
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': jsonlogger.JsonFormatter,
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
            },
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': settings.LOG_LEVEL,
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
            },
            'app_file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': str(LOGS_DIR / 'app.log'),
                'formatter': 'json',
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': str(LOGS_DIR / 'errors.log'),
                'formatter': 'json',
            },
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'app_file'],
                'level': settings.LOG_LEVEL,
                'propagate': False
            },
            'analytics': {
                'handlers': ['app_file'],
                'level': 'INFO',
                'propagate': False
            },
            'errors': {
                'handlers': ['error_file', 'console'],
                'level': 'ERROR',
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized", extra={
        "log_level": settings.LOG_LEVEL,
        "logs_directory": str(LOGS_DIR),
        "analytics_file": str(ANALYTICS_LOG_FILE)
    })

# Global analytics logger instance
analytics_logger = AnalyticsLogger()

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)