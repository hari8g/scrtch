from openai import OpenAI
from typing import Dict, Any, List, Optional, AsyncGenerator
from app.core.config import settings
from app.services.query_enhancement_service import QueryEnhancementService
import json


class ConversationalBotService:
    # the four core dimensions we need
    DIMENSIONS = ["product_type", "achievement_goal", "target_audience", "special_ingredients"]
    MAX_EXCHANGES = 4  # Maximum 4 exchanges (including initial query)

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.query_enhancer = QueryEnhancementService()
        self.remaining_dims: List[str] = []
        self.gathered_info: Dict[str, str] = {}
        self.exchange_count: int = 0

    async def _analyze_user_response(self, text: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Intelligently analyze what information the user has provided and what's still missing."""
        prompt = f"""
Analyze the user's response and the conversation context to determine:

1. What information has been provided (be specific)
2. What information is still missing
3. How to intelligently ask for the next piece of information
4. Whether we have enough information to proceed (considering we have limited exchanges)

Conversation so far:
{conversation_history}

User's latest response: "{text}"

IMPORTANT: We have a maximum of {self.MAX_EXCHANGES} exchanges total. 
If we're approaching this limit, be more aggressive about determining we have enough information.
Focus on the most critical missing information only.

Return a JSON object with:
- "provided_info": What specific information was given
- "missing_info": What's still needed (prioritize most important)
- "next_question_rationale": Why we should ask the next question
- "confidence": How confident we are (0-1)
- "ready_for_formulation": boolean (true if we have enough info or approaching limit)
- "exchange_count": Current exchange number
"""
        
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        try:
            result = json.loads(resp.choices[0].message.content)
            result["exchange_count"] = self.exchange_count
            return result
        except json.JSONDecodeError:
            return {
                "provided_info": "",
                "missing_info": [],
                "next_question_rationale": "Continue gathering information",
                "confidence": 0.0,
                "ready_for_formulation": False,
                "exchange_count": self.exchange_count
            }

    async def _detect_dimensions(self, text: str) -> List[str]:
        """Have GPT tell us which of the 4 dims the user's text already covers."""
        prompt = f"""
Analyze the user's text and identify which of these four categories are covered (return a JSON array of names):
 1. product_type (what specific product they want to create)
 2. achievement_goal (what they want to achieve/benefits they want)
 3. target_audience (who the product is for)
 4. special_ingredients (any specific ingredients they want to use)

IMPORTANT: Be strict about coverage. If the user says "I want a cream" but doesn't specify what type of cream (moisturizer, anti-aging, cleanser, etc.), then product_type is NOT fully covered.

User text:
\"\"\"{text}\"\"\"
"""
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        try:
            return json.loads(resp.choices[0].message.content)
        except json.JSONDecodeError:
            return []

    def _get_system_prompt(self) -> str:
        return (
            "You are an intelligent formulation assistant that learns from each user response. "
            "Ask exactly one question at a time, adapting based on what the user has already told you. "
            "Each question must be exactly one sentence and reference what the user said. "
            "Be conversational and build on previous information. "
            f"IMPORTANT: We have a maximum of {self.MAX_EXCHANGES} exchanges total. "
            "Be efficient and focus on the most critical missing information."
        )

    async def _generate_intelligent_question(
        self,
        conversation_history: List[Dict[str, str]],
        analysis: Dict[str, Any]
    ) -> str:
        """Generate an intelligent question based on what we've learned so far."""
        
        exchange_count = analysis.get("exchange_count", self.exchange_count)
        remaining_exchanges = self.MAX_EXCHANGES - exchange_count
        
        prompt = f"""
Based on the conversation analysis, generate the next intelligent question.

Analysis: {analysis}
Exchange count: {exchange_count}/{self.MAX_EXCHANGES}
Remaining exchanges: {remaining_exchanges}

Conversation history: {conversation_history}

Generate a single, conversational question that:
1. References what the user has already told us
2. Asks for the most critical missing information
3. Feels natural and builds on the conversation
4. Is exactly one sentence
5. Is efficient given we have limited exchanges remaining

Focus on the most important missing information that would be most valuable to gather next.
If we're near the limit, ask for the most critical piece of information only.
"""
        
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        return resp.choices[0].message.content.strip()

    async def start_conversation(self, initial_query: str) -> Dict[str, Any]:
        """Start a conversation with intelligent analysis."""
        try:
            self.exchange_count = 1  # Initial query counts as first exchange
            
            # 1) Analyze the initial query
            analysis = await self._analyze_user_response(initial_query, [{"role": "user", "content": initial_query}])
            
            # 2) Detect which dimensions are covered
            covered = await self._detect_dimensions(initial_query)
            self.remaining_dims = [d for d in self.DIMENSIONS if d not in covered]
            
            # 3) Store gathered information
            self.gathered_info = analysis.get("provided_info", {})
            
            # 4) Check if we already have enough information
            if analysis.get("ready_for_formulation", False) or self.exchange_count >= self.MAX_EXCHANGES:
                # Complete immediately if we have enough info or hit limit
                full = await self._reconstruct_query_from_conversation([{"role": "user", "content": initial_query}])
                enhanced = await self.query_enhancer.enhance_query(full)
                completion = await self._generate_completion_message(full, enhanced)
                
                return {
                    "conversation_id": self._generate_conversation_id(),
                    "current_query": full,
                    "is_sufficient": True,
                    "confidence_score": 1.0,
                    "enhanced_query": enhanced["enhanced_query"],
                    "intent_analysis": enhanced["intent_analysis"],
                    "conversation_history": [
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": initial_query},
                        {"role": "assistant", "content": completion}
                    ],
                    "ready_for_formulation": True,
                    "message": completion,
                    "questions_remaining": 0,
                    "gathered_info": self.gathered_info,
                    "exchange_count": self.exchange_count
                }
            
            # 5) Generate intelligent first question
            first_q = await self._generate_intelligent_question(
                [{"role": "user", "content": initial_query}],
                analysis
            )

            return {
                "conversation_id": self._generate_conversation_id(),
                "current_query": initial_query,
                "missing_information": analysis.get("missing_info", []),
                "confidence_score": analysis.get("confidence", 0.0),
                "is_sufficient": analysis.get("ready_for_formulation", False),
                "conversation_history": [
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": initial_query},
                    {"role": "assistant", "content": first_q}
                ],
                "next_question": first_q,
                "questions_remaining": len(analysis.get("missing_info", [])),
                "ready_for_formulation": False,
                "gathered_info": self.gathered_info,
                "exchange_count": self.exchange_count
            }
        except Exception as e:
            raise Exception(f"Failed to start conversation: {str(e)}")

    async def _is_vague_or_general(self, text: str) -> bool:
        prompt = f"""
Is the following user response vague, general, or non-committal (e.g., 'maybe', 'not sure', 'local flavor', 'spices', 'traditional', 'anything is fine', 'open to suggestions', etc.)? 
User response: "{text}"
Return true if it is vague or general, otherwise false. Respond with only 'true' or 'false'.
"""
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            answer = resp.choices[0].message.content.strip().lower()
            return answer.startswith('true')
        except Exception as e:
            print(f"[VAGUE DETECTION ERROR]: {e}")
            return False  # Default to not vague if error

    async def continue_conversation(
        self,
        conversation_id: str,
        user_response: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        try:
            # 1) Increment exchange count
            self.exchange_count += 1
            
            # 2) Add the user's answer
            conversation_history.append({"role": "user", "content": user_response})

            # 2.5) Check if the answer is vague/general and if so, skip further drilling
            try:
                is_vague = await self._is_vague_or_general(user_response)
            except Exception as e:
                print(f"[VAGUE CHECK ERROR]: {e}")
                is_vague = False
            try:
                analysis = await self._analyze_user_response(user_response, conversation_history)
            except Exception as e:
                print(f"[ANALYSIS ERROR]: {e}")
                analysis = {"provided_info": None, "missing_info": [], "confidence": 0.0, "ready_for_formulation": False}
            
            # 3) Update gathered information
            provided_info = analysis.get("provided_info")
            if isinstance(provided_info, dict):
                self.gathered_info.update(provided_info)
            elif isinstance(provided_info, str):
                # Optionally log or handle the string case
                pass

            # 4) Check if we have enough information or hit the limit
            if (analysis.get("ready_for_formulation", False) or 
                self.exchange_count >= self.MAX_EXCHANGES):
                try:
                    full = await self._reconstruct_query_from_conversation(conversation_history)
                    enhanced = await self.query_enhancer.enhance_query(full)
                    completion = await self._generate_completion_message(full, enhanced)
                    conversation_history.append({"role": "assistant", "content": completion})
                except Exception as e:
                    print(f"[FINALIZATION ERROR]: {e}")
                    completion = "There was an error generating your formulation. Please try again."
                    conversation_history.append({"role": "assistant", "content": completion})
                    enhanced = {"enhanced_query": "", "intent_analysis": {}}
                    full = ""
                return {
                    "conversation_id": conversation_id,
                    "current_query": full,
                    "is_sufficient": True,
                    "confidence_score": 1.0,
                    "enhanced_query": enhanced.get("enhanced_query", ""),
                    "intent_analysis": enhanced.get("intent_analysis", {}),
                    "conversation_history": conversation_history,
                    "ready_for_formulation": True,
                    "message": completion,
                    "questions_remaining": 0,
                    "gathered_info": self.gathered_info,
                    "exchange_count": self.exchange_count
                }

            # 5) If vague, skip to next dimension/question
            if is_vague:
                try:
                    next_q = await self._generate_intelligent_question(conversation_history, analysis)
                    conversation_history.append({"role": "assistant", "content": next_q})
                except Exception as e:
                    print(f"[NEXT QUESTION ERROR]: {e}")
                    next_q = "There was an error generating the next question. Please try again."
                    conversation_history.append({"role": "assistant", "content": next_q})
                return {
                    "conversation_id": conversation_id,
                    "current_query": await self._reconstruct_query_from_conversation(conversation_history),
                    "missing_information": analysis.get("missing_info", []),
                    "confidence_score": analysis.get("confidence", 0.0),
                    "is_sufficient": False,
                    "conversation_history": conversation_history,
                    "next_question": next_q,
                    "questions_remaining": len(analysis.get("missing_info", [])),
                    "ready_for_formulation": False,
                    "gathered_info": self.gathered_info,
                    "exchange_count": self.exchange_count
                }

            # 6) Otherwise, generate intelligent next question as usual
            try:
                next_q = await self._generate_intelligent_question(conversation_history, analysis)
                conversation_history.append({"role": "assistant", "content": next_q})
            except Exception as e:
                print(f"[NEXT QUESTION ERROR]: {e}")
                next_q = "There was an error generating the next question. Please try again."
                conversation_history.append({"role": "assistant", "content": next_q})
            return {
                "conversation_id": conversation_id,
                "current_query": await self._reconstruct_query_from_conversation(conversation_history),
                "missing_information": analysis.get("missing_info", []),
                "confidence_score": analysis.get("confidence", 0.0),
                "is_sufficient": False,
                "conversation_history": conversation_history,
                "next_question": next_q,
                "questions_remaining": len(analysis.get("missing_info", [])),
                "ready_for_formulation": False,
                "gathered_info": self.gathered_info,
                "exchange_count": self.exchange_count
            }
        except Exception as e:
            print(f"[CONVERSATION ERROR]: {e}")
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))

    async def stream_conversation_response(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Stream the conversation response for real-time feel."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Error: {str(e)}"

    async def _generate_completion_message(self, full_query: str, enhanced_data: Dict[str, Any]) -> str:
        """Generate a completion message."""
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"""The user has provided sufficient information: "{full_query}"

Generate a brief, enthusiastic completion message (exactly one sentence) that acknowledges we have enough information and will proceed to create their perfect formulation."""}
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    async def _reconstruct_query_from_conversation(self, conversation_history: List[Dict[str, str]]) -> str:
        """Reconstruct the full query from the conversation history."""
        # Extract all user messages (skip system message)
        user_messages = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
        combined_query = " ".join(user_messages)
        # Use AI to clean and structure the combined query
        prompt = f"""
        Based on the following conversation, create a single, concise, actionable paragraph for a formulation request. 
        - Do NOT include any pleasantries, 'please', 'request', 'additionally', or extra instructions.
        - Do NOT include any bullet points, lists, or further breakdowns.
        - Output ONLY the first, direct, actionable paragraph that summarizes the user's intent for the formulation.
        - No greetings, no closing statements, no extra context.
        - Be as brief and direct as possible.
        
        Conversation: {conversation_history}
        
        Output:
        - A single, concise, actionable paragraph (no more than 3-4 lines).
        """
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        result = response.choices[0].message.content.strip()
        # Post-process: Remove any lines starting with 'please', 'additionally', 'request', or similar
        import re
        lines = result.split('\n')
        filtered = []
        for line in lines:
            l = line.strip().lower()
            if l.startswith('please') or l.startswith('additionally') or l.startswith('request') or l.startswith('kindly'):
                continue
            filtered.append(line)
        # Only keep the first paragraph (up to a blank line or 3-4 lines)
        paragraph = []
        for line in filtered:
            if not line.strip():
                break
            paragraph.append(line)
            if len(paragraph) >= 4:
                break
        return ' '.join(paragraph).strip()
    
    async def aggregate_conversation_intent(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Aggregate the conversation to extract the user's complete intent."""
        try:
            # Extract all user responses (skip the initial query and system messages)
            user_responses = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
            
            # Create a structured summary of the conversation
            prompt = f"""
            Based on this conversation, create a structured summary of what the user wants:

            Conversation: {conversation_history}

            Extract and organize the information into these four dimensions:
            1. PRODUCT_TYPE: What specific product they want to create
            2. ACHIEVEMENT_GOAL: What they want to achieve/benefits they want
            3. TARGET_AUDIENCE: Who the product is for
            4. SPECIAL_INGREDIENTS: Any specific ingredients they want to use

            Return a JSON object with these four keys, each containing a clear summary.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            try:
                intent_summary = json.loads(response.choices[0].message.content)
                return {
                    "product_type": intent_summary.get("product_type", ""),
                    "achievement_goal": intent_summary.get("achievement_goal", ""),
                    "target_audience": intent_summary.get("target_audience", ""),
                    "special_ingredients": intent_summary.get("special_ingredients", ""),
                    "full_intent": await self._reconstruct_query_from_conversation(conversation_history)
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                full_intent = await self._reconstruct_query_from_conversation(conversation_history)
                return {
                    "product_type": "Product type not specified",
                    "achievement_goal": "Achievement goal not specified", 
                    "target_audience": "Target audience not specified",
                    "special_ingredients": "No special ingredients specified",
                    "full_intent": full_intent
                }
                
        except Exception as e:
            raise Exception(f"Failed to aggregate conversation intent: {str(e)}")
    
    def _generate_conversation_id(self) -> str:
        """Generate a unique conversation ID."""
        import uuid
        return str(uuid.uuid4())
    
    async def get_conversation_summary(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get a summary of the conversation and current understanding."""
        try:
            full_query = await self._reconstruct_query_from_conversation(conversation_history)
            validation_result = await self.query_enhancer.validate_query(full_query)
            
            return {
                "current_understanding": full_query,
                "confidence_score": validation_result.get("confidence_score", 0.0),
                "missing_information": validation_result.get("missing_information", []),
                "progress_percentage": self._calculate_progress(validation_result),
                "suggestions": validation_result.get("recommendations", [])
            }
        except Exception as e:
            raise Exception(f"Failed to get conversation summary: {str(e)}")
    
    def _calculate_progress(self, validation_result: Dict[str, Any]) -> int:
        """Calculate the progress percentage based on confidence and missing information."""
        confidence = validation_result.get("confidence_score", 0.0)
        missing_count = len(validation_result.get("missing_information", []))
        
        # Base progress on confidence score
        progress = int(confidence * 100)
        
        # Adjust based on missing information
        if missing_count == 0:
            progress = 100
        elif missing_count <= 2:
            progress = max(progress, 70)
        elif missing_count <= 4:
            progress = max(progress, 50)
        else:
            progress = max(progress, 30)
        
        return min(progress, 100) 