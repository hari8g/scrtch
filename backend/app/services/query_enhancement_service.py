from openai import OpenAI
from typing import Dict, Any, List
from app.core.config import settings


class QueryEnhancementService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    async def enhance_query(self, user_query: str) -> Dict[str, Any]:
        """
        Enhances a user query by understanding intent and adding missing context.
        Returns enhanced query with structured information.
        """
        try:
            # First, analyze the user's intent and extract key information
            intent_analysis = await self._analyze_intent(user_query)
            
            # Enhance the query based on the analysis
            enhanced_query = await self._create_enhanced_query(user_query, intent_analysis)
            
            return {
                "original_query": user_query,
                "enhanced_query": enhanced_query,
                "intent_analysis": intent_analysis,
                "missing_context": intent_analysis.get("missing_context", []),
                "suggested_improvements": intent_analysis.get("suggestions", [])
            }
            
        except Exception as e:
            raise Exception(f"Failed to enhance query: {str(e)}")
    
    async def _analyze_intent(self, query: str) -> Dict[str, Any]:
        """Analyze user intent and extract key information from the query."""
        
        analysis_prompt = f"""
        Analyze the following user query for natural ingredient formulation and extract key information:

        User Query: "{query}"

        Please provide a JSON response with the following structure:
        {{
            "intent": "string describing the main goal (e.g., 'skincare', 'hair care', 'body care', 'makeup', 'supplements')",
            "target_audience": "string describing who this is for (e.g., 'sensitive skin', 'dry hair', 'aging skin', 'acne-prone')",
            "product_type": "string describing the product type (e.g., 'cleanser', 'moisturizer', 'serum', 'mask', 'shampoo')",
            "specific_concerns": ["list of specific skin/hair/body concerns"],
            "ingredient_preferences": ["list of preferred ingredient types (e.g., 'organic', 'vegan', 'fragrance-free')"],
            "missing_context": ["list of important information that seems to be missing"],
            "suggestions": ["list of suggestions to improve the query"],
            "complexity_level": "string describing the formulation complexity needed"
        }}

        Focus on natural, clean, and organic ingredients. Be specific about what information is missing.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        try:
            import json
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback analysis
            return self._fallback_intent_analysis(query)
    
    async def _create_enhanced_query(self, original_query: str, intent_analysis: Dict[str, Any]) -> str:
        """Create an enhanced query based on the intent analysis."""
        
        enhancement_prompt = f"""
        Based on the following analysis, create a comprehensive, detailed query for generating natural ingredient formulations:

        Original Query: "{original_query}"
        
        Intent Analysis: {intent_analysis}
        
        Create an enhanced query that:
        1. Includes all the specific details from the intent analysis
        2. Adds missing context automatically
        3. Specifies the type of ingredients needed (natural, organic, clean)
        4. Includes safety considerations
        5. Mentions any specific benefits or properties required
        6. Specifies the formulation complexity level
        7. Includes any relevant contraindications or warnings
        
        Return only the enhanced query text, no JSON formatting.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": enhancement_prompt}],
            temperature=0.4
        )
        
        return response.choices[0].message.content.strip()
    
    def _fallback_intent_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback analysis when JSON parsing fails."""
        return {
            "intent": "general formulation",
            "target_audience": "general",
            "product_type": "formulation",
            "specific_concerns": [],
            "ingredient_preferences": ["natural", "clean"],
            "missing_context": ["specific skin type", "product type", "specific concerns"],
            "suggestions": ["Add skin type", "Specify product type", "Mention specific concerns"],
            "complexity_level": "basic"
        }
    
    async def get_query_suggestions(self, user_query: str) -> List[str]:
        """Get suggestions for improving the user query."""
        try:
            intent_analysis = await self._analyze_intent(user_query)
            return intent_analysis.get("suggestions", [])
        except Exception as e:
            return ["Please provide more specific details about your formulation needs"]
    
    async def validate_query(self, user_query: str) -> Dict[str, Any]:
        """Validate if a query has sufficient information for formulation."""
        try:
            intent_analysis = await self._analyze_intent(user_query)
            missing_context = intent_analysis.get("missing_context", [])
            
            return {
                "is_sufficient": len(missing_context) == 0,
                "missing_information": missing_context,
                "confidence_score": self._calculate_confidence(intent_analysis),
                "recommendations": intent_analysis.get("suggestions", [])
            }
        except Exception as e:
            return {
                "is_sufficient": False,
                "missing_information": ["Unable to analyze query"],
                "confidence_score": 0.0,
                "recommendations": ["Please provide more specific details"]
            }
    
    def _calculate_confidence(self, intent_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score based on completeness of information."""
        required_fields = ["intent", "target_audience", "product_type"]
        provided_fields = sum(1 for field in required_fields if intent_analysis.get(field))
        
        # Base score from required fields
        base_score = provided_fields / len(required_fields)
        
        # Bonus for specific concerns and preferences
        specific_concerns = len(intent_analysis.get("specific_concerns", []))
        preferences = len(intent_analysis.get("ingredient_preferences", []))
        
        bonus_score = min((specific_concerns + preferences) * 0.1, 0.3)
        
        return min(base_score + bonus_score, 1.0) 