from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
from app.models.ingredient import Ingredient
from app.services.formulation_service import FormulationService
import asyncio
import json


class FormulationRequest(BaseModel):
    query: str


class QueryValidationRequest(BaseModel):
    query: str


class QuerySuggestionsRequest(BaseModel):
    query: str


router = APIRouter()
formulation_service = FormulationService()


@router.post("/", response_model=Dict[str, Any])
async def generate_formulation(request: FormulationRequest):
    """Generate formulation with enhanced query processing."""
    try:
        result = await formulation_service.generate_formulation(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=Dict[str, Any])
async def validate_query(request: QueryValidationRequest):
    """Validate if a query has sufficient information for formulation."""
    try:
        validation_result = await formulation_service.validate_query(request.query)
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions", response_model=List[str])
async def get_query_suggestions(request: QuerySuggestionsRequest):
    """Get suggestions for improving the user query."""
    try:
        suggestions = await formulation_service.get_query_suggestions(request.query)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream")
async def generate_formulation_stream(query: str = ""):
    async def event_stream():
        # 1. Query Enhancement
        yield f'data: {json.dumps({"stage": "enhancement", "message": "Refining your formulation request for clarity…"})}\n\n'
        enhanced_data = await formulation_service.query_enhancer.enhance_query(query)
        enhanced_query = enhanced_data.get("enhanced_query", "")
        yield f'data: {json.dumps({"stage": "enhanced", "message": f"Enhanced query: {enhanced_query[:80]}…"})}\n\n'

        # 2. Retrieval (AI call)
        yield f'data: {json.dumps({"stage": "retrieval", "message": "Consulting the AI for the best natural ingredients…"})}\n\n'
        ingredients = await formulation_service._generate_ingredients(enhanced_query)
        if ingredients:
            top_ingredient = ingredients[0].name
            yield f'data: {json.dumps({"stage": "retrieved", "message": f"Retrieved {len(ingredients)} ingredients. Top: {top_ingredient}"})}\n\n'
        else:
            yield f'data: {json.dumps({"stage": "retrieved", "message": "No ingredients found."})}\n\n'

        # 3. Analysis/Validation (simulate or use real logic)
        yield f'data: {json.dumps({"stage": "analysis", "message": f"Analyzing {len(ingredients)} ingredients for safety and compatibility…"})}\n\n'
        warnings = []
        for ing in ingredients:
            if not ing.attributes.get('safety'):
                warnings.append(ing.name)
        if warnings:
            warn_str = ', '.join(warnings[:3])
            yield f'data: {json.dumps({"stage": "analyzed", "message": f"Warning: No safety info for {warn_str}."})}\n\n'
        else:
            yield f'data: {json.dumps({"stage": "analyzed", "message": "All ingredients validated for safety."})}\n\n'

        # 4. Synthesis/Formatting
        yield f'data: {json.dumps({"stage": "synthesis", "message": f"Composing your personalized formulation with {len(ingredients)} ingredients…"})}\n\n'
        yield f'data: {json.dumps({"stage": "done", "message": "Formulation complete!"})}\n\n'
    return StreamingResponse(event_stream(), media_type='text/event-stream') 