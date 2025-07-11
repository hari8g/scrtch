import { API_CONFIG } from '../config/api';

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ConversationResponse {
  conversation_id: string;
  current_query: string;
  missing_information: string[];
  confidence_score: number;
  is_sufficient: boolean;
  next_question?: string;
  conversation_history: ConversationMessage[];
  ready_for_formulation?: boolean;
  enhanced_query?: string;
  intent_analysis?: any;
  message?: string;
  questions_remaining?: number;
  gathered_info?: any;
  exchange_count?: number;
}

export interface ConversationSummary {
  current_understanding: string;
  confidence_score: number;
  missing_information: string[];
  progress_percentage: number;
  suggestions: string[];
}

export interface ConversationIntent {
  product_type: string;
  achievement_goal: string;
  target_audience: string;
  special_ingredients: string;
  full_intent: string;
}

export async function startConversation(initial_query: string): Promise<ConversationResponse> {
  const res = await fetch(API_CONFIG.CONVERSATION_ENDPOINTS.START, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ initial_query }),
  });
  if (!res.ok) throw new Error('Failed to start conversation');
  return res.json();
}

export async function continueConversation(
  conversation_id: string,
  user_response: string,
  conversation_history: ConversationMessage[]
): Promise<ConversationResponse> {
  const res = await fetch(API_CONFIG.CONVERSATION_ENDPOINTS.CONTINUE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      conversation_id, 
      user_response, 
      conversation_history
    }),
  });
  if (!res.ok) throw new Error('Failed to continue conversation');
  return res.json();
}

export async function aggregateConversationIntent(
  conversation_history: ConversationMessage[]
): Promise<ConversationIntent> {
  const res = await fetch(API_CONFIG.CONVERSATION_ENDPOINTS.AGGREGATE_INTENT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_history }),
  });
  if (!res.ok) throw new Error('Failed to aggregate conversation intent');
  return res.json();
}

export async function streamConversation(messages: ConversationMessage[]): Promise<ReadableStream> {
  const res = await fetch(API_CONFIG.CONVERSATION_ENDPOINTS.STREAM, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) throw new Error('Failed to stream conversation');
  return res.body!;
}

export async function getConversationSummary(
  conversation_history: ConversationMessage[]
): Promise<ConversationSummary> {
  const res = await fetch(API_CONFIG.CONVERSATION_ENDPOINTS.SUMMARY, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_history }),
  });
  if (!res.ok) throw new Error('Failed to get conversation summary');
  return res.json();
} 