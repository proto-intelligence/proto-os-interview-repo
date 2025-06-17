from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from typing import Generator

from app.integrations.openrouter.client import OpenRouterClient
from app.integrations.openrouter.schemas import (
    CompletionRequest,
    CompletionResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    GenerationResponse
)

import requests

router = APIRouter()

client = OpenRouterClient()

@router.post("/completions", response_model=CompletionResponse, tags=["OpenRouter"])
def create_completion(payload: CompletionRequest):
    try:
        return client.completion(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/completions", response_model=ChatCompletionResponse, tags=["OpenRouter"])
def create_chat_completion(payload: ChatCompletionRequest):
    try:
        return client.chat_completion(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/completions/stream", tags=["OpenRouter"])
def stream_chat_completion(payload: ChatCompletionRequest):
    try:
        def event_generator() -> Generator[str, None, None]:
            for chunk in client.stream_chat_completion(payload):
                yield f"data: {chunk}\n\n"
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/completions/schema", tags=["OpenRouter"])
def structured_chat_completion(payload: ChatCompletionRequest):
    try:
        if not payload.model:
            raise HTTPException(status_code=400, detail="Model must be specified")
        return client.chat_completion_with_schema(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/generations", response_model=GenerationResponse, tags=["OpenRouter"])
def get_generation(generation_id: str = Query(..., description="ID of the generation")):
    try:
        return client.get_generation(generation_id)
    except requests.HTTPError as http_err:
        if http_err.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Generation ID '{generation_id}' not found.")
        else:
            raise HTTPException(status_code=http_err.response.status_code, detail=http_err.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error.")

@router.get("/models", response_model=list[str], tags=["OpenRouter"])
def list_models():
    try:
        return client.list_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/endpoints", response_model=list[dict], tags=["OpenRouter"])
def list_model_endpoints(model_id: str = Query(..., description="Model identifier")):
    try:
        endpoints = client.list_model_endpoints(model_id)
        return endpoints
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/credits", tags=["OpenRouter"])
def get_credits():
    try:
        return client.get_credits()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))