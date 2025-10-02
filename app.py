import uuid
import time
from fastapi import FastAPI, HTTPException
from fastapi.requests import Request
from models import BotRequest, BotResponse, ErrorResponse
from ai_nlu import ai_nlu
import crm_client
from settings import settings
from logger_config import setup_logging, analytics_logger, get_logger

# Initialize logging system
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title='AI Bot Service',
    description='Enhanced AI-powered bot service with OpenAI integration',
    version='2.0.0'
)

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("AI Bot Service starting up", extra={
        "use_ai_nlu": settings.USE_AI_NLU,
        "crm_base_url": settings.CRM_BASE_URL,
        "max_transcript_length": settings.MAX_TRANSCRIPT_LENGTH
    })

@app.post('/bot/handle', response_model=BotResponse, responses={400: {'model': ErrorResponse}, 500: {'model': ErrorResponse}})
def handle(request: BotRequest):
    """
    Handle bot requests with enhanced AI-powered NLU and comprehensive logging.
    
    This endpoint:
    1. Validates the input transcript
    2. Uses AI-enhanced NLU for intent classification and entity extraction
    3. Calls appropriate CRM endpoints based on intent
    4. Logs all interactions for analytics
    5. Returns structured response with confidence scores
    
    Args:
        request: BotRequest containing transcript and optional metadata
        
    Returns:
        BotResponse with intent, entities, CRM call details, and result
        
    Raises:
        HTTPException: For validation errors or CRM failures
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info("Processing bot request", extra={
        "request_id": request_id,
        "transcript_length": len(request.transcript) if request.transcript else 0
    })
    
    transcript = request.transcript
    
    # Input validation
    if not transcript or len(transcript) > settings.MAX_TRANSCRIPT_LENGTH:
        error_msg = 'Transcript missing or too long'
        logger.warning("Validation error", extra={
            "request_id": request_id,
            "error": error_msg,
            "transcript_length": len(transcript) if transcript else 0
        })
        
        analytics_logger.log_interaction(
            request_id=request_id,
            transcript=transcript or "",
            intent="VALIDATION_ERROR",
            entities={},
            success=False,
            error_message=error_msg,
            response_time_ms=(time.time() - start_time) * 1000
        )
        
        raise HTTPException(status_code=400, detail={
            'type': 'VALIDATION_ERROR',
            'details': error_msg
        })
    
    # Parse transcript with AI-enhanced NLU
    try:
        parsed = ai_nlu.parse_transcript(transcript)
        intent = parsed['intent']
        entities = parsed['entities']
        confidence = parsed.get('confidence')
        ai_enhanced = parsed.get('ai_enhanced', False)
        
        logger.info("NLU parsing completed", extra={
            "request_id": request_id,
            "intent": intent,
            "entity_count": len(entities),
            "confidence": confidence,
            "ai_enhanced": ai_enhanced
        })
        
    except Exception as e:
        error_msg = f'NLU parsing failed: {str(e)}'
        logger.error("NLU parsing error", extra={
            "request_id": request_id,
            "error": error_msg
        })
        
        analytics_logger.log_interaction(
            request_id=request_id,
            transcript=transcript,
            intent="NLU_ERROR",
            entities={},
            success=False,
            error_message=error_msg,
            response_time_ms=(time.time() - start_time) * 1000
        )
        
        raise HTTPException(status_code=500, detail={
            'type': 'NLU_ERROR',
            'details': error_msg
        })
    
    # Handle different intents
    crm_call_result = None
    result = None
    
    try:
        if intent == 'LEAD_CREATE':
            if not entities.get('name') or not entities.get('phone') or not entities.get('city'):
                error_msg = 'Missing name, phone, or city for LEAD_CREATE'
                logger.warning("Entity validation error", extra={
                    "request_id": request_id,
                    "intent": intent,
                    "missing_entities": [k for k in ['name', 'phone', 'city'] if not entities.get(k)]
                })
                
                analytics_logger.log_interaction(
                    request_id=request_id,
                    transcript=transcript,
                    intent=intent,
                    entities=entities,
                    confidence=confidence,
                    success=False,
                    error_message=error_msg,
                    response_time_ms=(time.time() - start_time) * 1000,
                    ai_enhanced=ai_enhanced
                )
                
                raise HTTPException(status_code=400, detail={
                    'type': 'VALIDATION_ERROR',
                    'details': error_msg
                })
            
            resp = crm_client.create_lead(
                entities['name'], 
                entities['phone'], 
                entities['city'], 
                entities.get('source')
            )
            
            crm_call_result = {
                'endpoint': '/crm/leads',
                'method': 'POST',
                'status_code': resp.status_code
            }
            
            if resp.status_code >= 200 and resp.status_code < 300:
                data = resp.json()
                result = {
                    'message': 'Lead created',
                    'lead_id': data.get('lead_id')
                }
                logger.info("Lead created successfully", extra={
                    "request_id": request_id,
                    "lead_id": data.get('lead_id')
                })
            else:
                error_msg = f'CRM returned {resp.status_code}: {resp.text}'
                logger.error("CRM API error", extra={
                    "request_id": request_id,
                    "crm_status": resp.status_code,
                    "crm_response": resp.text
                })
                
                analytics_logger.log_interaction(
                    request_id=request_id,
                    transcript=transcript,
                    intent=intent,
                    entities=entities,
                    confidence=confidence,
                    success=False,
                    error_message=error_msg,
                    response_time_ms=(time.time() - start_time) * 1000,
                    crm_call_result=crm_call_result,
                    ai_enhanced=ai_enhanced
                )
                
                raise HTTPException(status_code=500, detail={
                    'type': 'CRM_ERROR',
                    'details': error_msg
                })
        
        elif intent == 'VISIT_SCHEDULE':
            if not entities.get('lead_id') or not entities.get('visit_time'):
                error_msg = 'Missing lead_id or visit_time for VISIT_SCHEDULE'
                logger.warning("Entity validation error", extra={
                    "request_id": request_id,
                    "intent": intent,
                    "missing_entities": [k for k in ['lead_id', 'visit_time'] if not entities.get(k)]
                })
                
                analytics_logger.log_interaction(
                    request_id=request_id,
                    transcript=transcript,
                    intent=intent,
                    entities=entities,
                    confidence=confidence,
                    success=False,
                    error_message=error_msg,
                    response_time_ms=(time.time() - start_time) * 1000,
                    ai_enhanced=ai_enhanced
                )
                
                raise HTTPException(status_code=400, detail={
                    'type': 'VALIDATION_ERROR',
                    'details': error_msg
                })
            
            resp = crm_client.schedule_visit(
                entities['lead_id'], 
                entities['visit_time'], 
                entities.get('notes')
            )
            
            crm_call_result = {
                'endpoint': '/crm/visits',
                'method': 'POST',
                'status_code': resp.status_code
            }
            
            if resp.status_code >= 200 and resp.status_code < 300:
                data = resp.json()
                result = {
                    'message': 'Visit scheduled',
                    'visit_id': data.get('visit_id')
                }
                logger.info("Visit scheduled successfully", extra={
                    "request_id": request_id,
                    "visit_id": data.get('visit_id'),
                    "lead_id": entities['lead_id']
                })
            else:
                error_msg = f'CRM returned {resp.status_code}: {resp.text}'
                logger.error("CRM API error", extra={
                    "request_id": request_id,
                    "crm_status": resp.status_code,
                    "crm_response": resp.text
                })
                
                analytics_logger.log_interaction(
                    request_id=request_id,
                    transcript=transcript,
                    intent=intent,
                    entities=entities,
                    confidence=confidence,
                    success=False,
                    error_message=error_msg,
                    response_time_ms=(time.time() - start_time) * 1000,
                    crm_call_result=crm_call_result,
                    ai_enhanced=ai_enhanced
                )
                
                raise HTTPException(status_code=500, detail={
                    'type': 'CRM_ERROR',
                    'details': error_msg
                })
        
        elif intent == 'LEAD_UPDATE':
            if not entities.get('lead_id') or not entities.get('status'):
                error_msg = 'Missing lead_id or status for LEAD_UPDATE'
                logger.warning("Entity validation error", extra={
                    "request_id": request_id,
                    "intent": intent,
                    "missing_entities": [k for k in ['lead_id', 'status'] if not entities.get(k)]
                })
                
                analytics_logger.log_interaction(
                    request_id=request_id,
                    transcript=transcript,
                    intent=intent,
                    entities=entities,
                    confidence=confidence,
                    success=False,
                    error_message=error_msg,
                    response_time_ms=(time.time() - start_time) * 1000,
                    ai_enhanced=ai_enhanced
                )
                
                raise HTTPException(status_code=400, detail={
                    'type': 'VALIDATION_ERROR',
                    'details': error_msg
                })
            
            resp = crm_client.update_lead_status(
                entities['lead_id'], 
                entities['status'], 
                entities.get('notes')
            )
            
            crm_call_result = {
                'endpoint': f"/crm/leads/{{lead_id}}/status",
                'method': 'POST',
                'status_code': resp.status_code
            }
            
            if resp.status_code >= 200 and resp.status_code < 300:
                data = resp.json()
                result = {
                    'message': 'Lead status updated',
                    'status': data.get('status')
                }
                logger.info("Lead status updated successfully", extra={
                    "request_id": request_id,
                    "lead_id": entities['lead_id'],
                    "new_status": entities['status']
                })
            else:
                error_msg = f'CRM returned {resp.status_code}: {resp.text}'
                logger.error("CRM API error", extra={
                    "request_id": request_id,
                    "crm_status": resp.status_code,
                    "crm_response": resp.text
                })
                
                analytics_logger.log_interaction(
                    request_id=request_id,
                    transcript=transcript,
                    intent=intent,
                    entities=entities,
                    confidence=confidence,
                    success=False,
                    error_message=error_msg,
                    response_time_ms=(time.time() - start_time) * 1000,
                    crm_call_result=crm_call_result,
                    ai_enhanced=ai_enhanced
                )
                
                raise HTTPException(status_code=500, detail={
                    'type': 'CRM_ERROR',
                    'details': error_msg
                })
        
        else:
            # Unknown intent handling
            result = {'message': 'Could not determine intent'}
            logger.info("Unknown intent detected", extra={
                "request_id": request_id,
                "intent": intent,
                "confidence": confidence
            })
        
        # Log successful interaction
        response_time = (time.time() - start_time) * 1000
        analytics_logger.log_interaction(
            request_id=request_id,
            transcript=transcript,
            intent=intent,
            entities=entities,
            confidence=confidence,
            success=True,
            response_time_ms=response_time,
            crm_call_result=crm_call_result,
            ai_enhanced=ai_enhanced
        )
        
        logger.info("Request processed successfully", extra={
            "request_id": request_id,
            "intent": intent,
            "response_time_ms": response_time
        })
        
        # Build enhanced response
        response = BotResponse(
            intent=intent,
            entities=entities,
            crm_call=crm_call_result,
            result=result
        )
        
        # Add AI-specific metadata to response if available
        if hasattr(response, '__dict__'):
            if confidence is not None:
                response.__dict__['confidence'] = confidence
            if ai_enhanced:
                response.__dict__['ai_enhanced'] = ai_enhanced
            if parsed.get('multiple_requests_detected'):
                response.__dict__['multiple_requests_detected'] = True
                response.__dict__['total_requests'] = parsed.get('total_requests')
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (already logged)
        raise
    except Exception as e:
        # Handle unexpected errors
        error_msg = f'Unexpected error: {str(e)}'
        logger.error("Unexpected error", extra={
            "request_id": request_id,
            "error": error_msg,
            "exception_type": type(e).__name__
        })
        
        analytics_logger.log_interaction(
            request_id=request_id,
            transcript=transcript,
            intent=intent,
            entities=entities or {},
            confidence=confidence,
            success=False,
            error_message=error_msg,
            response_time_ms=(time.time() - start_time) * 1000,
            ai_enhanced=ai_enhanced
        )
        
        raise HTTPException(status_code=500, detail={
            'type': 'INTERNAL_ERROR',
            'details': error_msg
        })
