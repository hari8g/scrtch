// API Configuration
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_CONFIG = {
  BASE_URL: API_BASE_URL,
  FORMULATION_ENDPOINTS: {
    GENERATE: `${API_BASE_URL}/formulation/`,
    VALIDATE: `${API_BASE_URL}/formulation/validate`,
    SUGGESTIONS: `${API_BASE_URL}/formulation/suggestions`,
    STREAM: `${API_BASE_URL}/formulation/stream`,
  },
  CONVERSATION_ENDPOINTS: {
    START: `${API_BASE_URL}/conversation/start`,
    CONTINUE: `${API_BASE_URL}/conversation/continue`,
    AGGREGATE_INTENT: `${API_BASE_URL}/conversation/aggregate-intent`,
    STREAM: `${API_BASE_URL}/conversation/stream`,
    SUMMARY: `${API_BASE_URL}/conversation/summary`,
  },
}; 