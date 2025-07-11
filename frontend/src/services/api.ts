import { API_CONFIG } from '../config/api';

export interface Ingredient {
  name: string;
  attributes: Record<string, any>;
}

export interface FormulationResponse {
  ingredients: Ingredient[];
  query_analysis: {
    original_query: string;
    enhanced_query: string;
    intent_analysis: any;
    missing_context: string[];
    suggested_improvements: string[];
  };
  original_query: string;
  enhanced_query: string;
}

export interface QueryValidationResponse {
  is_sufficient: boolean;
  missing_information: string[];
  confidence_score: number;
  recommendations: string[];
}

export async function generateFormulation(query: string): Promise<FormulationResponse> {
  const res = await fetch(API_CONFIG.FORMULATION_ENDPOINTS.GENERATE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error('Failed to generate formulation');
  return res.json();
}

export async function validateQuery(query: string): Promise<QueryValidationResponse> {
  const res = await fetch(API_CONFIG.FORMULATION_ENDPOINTS.VALIDATE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error('Failed to validate query');
  return res.json();
}

export async function getQuerySuggestions(query: string): Promise<string[]> {
  const res = await fetch(API_CONFIG.FORMULATION_ENDPOINTS.SUGGESTIONS, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error('Failed to get suggestions');
  return res.json();
} 