// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// API endpoints
export const API_ENDPOINTS = {
  LOGIN: `${API_BASE_URL}/login`,
  DASHBOARD: `${API_BASE_URL}/api/dashboard`,
  TEST_CASES: `${API_BASE_URL}/api/testcases`,
  TEST_CASE_BY_ID: (testcase_id: number) => `${API_BASE_URL}/api/testcases/${testcase_id}`,
  TEST_CASES_UPDATE_BY_ID: (testcase_id: number) => `${API_BASE_URL}/api/testcases/${testcase_id}`,

  STRATEGIES: `${API_BASE_URL}/api/strategies`,
  RESPONSES: `${API_BASE_URL}/api/responses`,
  PROMPTS: `${API_BASE_URL}/api/prompts`,
  LLM_PROMPTS: `${API_BASE_URL}/api/llmPrompts`,
};

