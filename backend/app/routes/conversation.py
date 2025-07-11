from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.conversational_bot_service import ConversationalBotService
import logging


class StartConversationRequest(BaseModel):
    initial_query: str


class ContinueConversationRequest(BaseModel):
    conversation_id: str
    user_response: str
    conversation_history: List[Dict[str, str]]


class GetSummaryRequest(BaseModel):
    conversation_history: List[Dict[str, str]]


class AggregateIntentRequest(BaseModel):
    conversation_history: List[Dict[str, str]]


class StreamRequest(BaseModel):
    messages: List[Dict[str, str]]


router = APIRouter()
conversational_bot = ConversationalBotService()


@router.post("/start", response_model=Dict[str, Any])
async def start_conversation(request: StartConversationRequest):
    """Start a new conversational formulation session."""
    try:
        result = await conversational_bot.start_conversation(request.initial_query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continue", response_model=Dict[str, Any])
async def continue_conversation(request: ContinueConversationRequest):
    """Continue the conversation with user's response."""
    try:
        result = await conversational_bot.continue_conversation(
            request.conversation_id,
            request.user_response,
            request.conversation_history
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/aggregate-intent", response_model=Dict[str, Any])
async def aggregate_conversation_intent(request: AggregateIntentRequest):
    """Aggregate the conversation to extract the user's complete intent."""
    try:
        result = await conversational_bot.aggregate_conversation_intent(request.conversation_history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_conversation(request: StreamRequest):
    """Stream conversation response for real-time feel."""
    import threading
    from queue import Queue
    import logging
    
    def sync_stream():
        try:
            response = conversational_bot.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=request.messages,
                temperature=0.7,
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
        except Exception as e:
            logging.error(f"OpenAI API error in streaming: {str(e)}")
            yield f"data: Error: Unable to generate response. Please try again.\n\n"
    
    async def async_gen():
        q = Queue()
        def worker():
            try:
                for chunk in sync_stream():
                    q.put(chunk)
                q.put(None)
            except Exception as e:
                logging.error(f"Worker thread error: {str(e)}")
                q.put(f"data: Error: {str(e)}\n\n")
                q.put(None)
        
        threading.Thread(target=worker, daemon=True).start()
        while True:
            try:
                chunk = await run_in_threadpool(q.get)
                if chunk is None:
                    break
                yield chunk
            except Exception as e:
                logging.error(f"Async generator error: {str(e)}")
                yield f"data: Error: {str(e)}\n\n"
                break
    
    return StreamingResponse(
        async_gen(), 
        media_type="text/plain", 
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.post("/summary", response_model=Dict[str, Any])
async def get_conversation_summary(request: GetSummaryRequest):
    """Get a summary of the current conversation progress."""
    try:
        result = await conversational_bot.get_conversation_summary(request.conversation_history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 