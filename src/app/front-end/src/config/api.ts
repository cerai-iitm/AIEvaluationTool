// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// API endpoints
export const API_ENDPOINTS = {
  LOGIN: `${API_BASE_URL}/login`,
  DASHBOARD: `${API_BASE_URL}/api/dashboard/summary`,
  TEST_CASES: `${API_BASE_URL}/api/testcases/t`,
  TEST_CASE_BY_ID: (id: number) => `${API_BASE_URL}/api/testcases/${id}`,
  RESPONSES: `${API_BASE_URL}/api/responses`,
};

