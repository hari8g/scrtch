from openai import OpenAI
import json
from typing import List, Dict, Any
from app.core.config import settings
from app.models.ingredient import Ingredient
from app.services.query_enhancement_service import QueryEnhancementService


class FormulationService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.query_enhancer = QueryEnhancementService()
    
    async def generate_formulation(self, query: str) -> Dict[str, Any]:
        """
        Generate formulation with enhanced query processing.
        Returns both ingredients and query analysis.
        """
        try:
            # First, enhance the user query
            enhanced_data = await self.query_enhancer.enhance_query(query)
            enhanced_query = enhanced_data["enhanced_query"]
            
            # Generate ingredients using the enhanced query
            ingredients = await self._generate_ingredients(enhanced_query)
            
            return {
                "ingredients": ingredients,
                "query_analysis": enhanced_data,
                "original_query": query,
                "enhanced_query": enhanced_query
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate formulation: {str(e)}")
    
    async def _generate_ingredients(self, enhanced_query: str) -> List[Ingredient]:
        """Generate ingredients using the enhanced query."""
        
        formulation_prompt = f"""
        Based on the following detailed query, provide a comprehensive list of 100% clean, natural ingredients for formulation.

        Query: {enhanced_query}

        Return ONLY a valid JSON array of objects with this exact structure (no additional text, no markdown formatting):
        [
            {{
                "name": "ingredient name",
                "attributes": {{
                    "benefits": "specific benefits and properties",
                    "usage": "how to use in formulation",
                    "safety": "safety considerations and warnings",
                    "concentration": "recommended concentration range",
                    "compatibility": "what ingredients it works well with",
                    "contraindications": "when not to use",
                    "source": "natural source information",
                    "certification": "organic/certification status if applicable"
                }}
            }}
        ]

        Focus on:
        - 100% natural and clean ingredients
        - Organic and sustainable sources when possible
        - Safety and efficacy
        - Proper usage guidelines
        - Compatibility information
        - Concentration recommendations
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": formulation_prompt}],
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean the content to extract JSON
        content = self._extract_json_from_response(content)
        
        try:
            ingredients_data = json.loads(content)
            ingredients = []
            for item in ingredients_data:
                if isinstance(item, dict) and 'name' in item:
                    ingredients.append(Ingredient(
                        name=item['name'],
                        attributes=item.get('attributes', {})
                    ))
            return ingredients
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Content: {content}")
            # Fallback: parse the text response manually
            return self._parse_text_response(content)
    
    def _extract_json_from_response(self, content: str) -> str:
        """Extract JSON from the response, handling various formats."""
        # Remove markdown code blocks
        content = content.replace('```json', '').replace('```', '').strip()
        
        # Find the first [ and last ] to extract the array
        start = content.find('[')
        end = content.rfind(']')
        
        if start != -1 and end != -1 and end > start:
            return content[start:end + 1]
        
        return content
    
    def _parse_text_response(self, content: str) -> List[Ingredient]:
        """Fallback method to parse text response when JSON parsing fails"""
        ingredients = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Simple parsing - assume first word is ingredient name
                parts = line.split(':', 1)
                if len(parts) >= 1:
                    name = parts[0].strip()
                    attributes = {}
                    if len(parts) > 1:
                        attributes['description'] = parts[1].strip()
                    ingredients.append(Ingredient(name=name, attributes=attributes))
        
        return ingredients
    
    async def get_query_suggestions(self, query: str) -> List[str]:
        """Get suggestions for improving the user query."""
        return await self.query_enhancer.get_query_suggestions(query)
    
    async def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate if a query has sufficient information."""
        return await self.query_enhancer.validate_query(query) 