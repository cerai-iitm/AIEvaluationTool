// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// API endpoints
export const API_ENDPOINTS = {
  LOGIN: `${API_BASE_URL}/login`,
  DASHBOARD: `${API_BASE_URL}/api/dashboard`,
  TEST_CASES: `${API_BASE_URL}/api/testcases`,
  TEST_CASE_BY_ID: (testcase_id: number) => `${API_BASE_URL}/api/testcases/${testcase_id}`,
  TEST_CASES_UPDATE_BY_ID: (testcase_id: number) => `${API_BASE_URL}/api/testcases/${testcase_id}`,
  TEST_CASE_CREATE: `${API_BASE_URL}/api/testcases/create`,

  TARGETS: `${API_BASE_URL}/api/targets`,
  TARGET_TYPES: `${API_BASE_URL}/api/targets/target/types`,
  TARGET_BY_ID: (target_id: number) => `${API_BASE_URL}/api/targets/${target_id}`,

  //STRATEGIES: `${API_BASE_URL}/api/strategies`,
  RESPONSES: `${API_BASE_URL}/api/responses`,
  PROMPTS: `${API_BASE_URL}/api/prompts`,
  LLM_PROMPTS: `${API_BASE_URL}/api/llmPrompts`,
  CURRENT_USER: `${API_BASE_URL}/api/users/me`,
  USERS: `${API_BASE_URL}/api/users`,
  USER_ACTIVITY: (username: string) => `${API_BASE_URL}/api/users/${username}`,
  ENTITY_ACTIVITY: (entityType: string) => `${API_BASE_URL}/api/users/activity/${entityType}`,
  
  LANGUAGES: `${API_BASE_URL}/api/languages`,
  LANGUAGE_BY_ID: (lang_id: number) => `${API_BASE_URL}/api/languages/${lang_id}`,
  LANGUAGE_CREATE: `${API_BASE_URL}/api/languages/create`,
  LANGUAGE_UPDATE: (lang_id: number) => `${API_BASE_URL}/api/languages/update/${lang_id}`,
  LANGUAGE_DELETE: (lang_id: number) => `${API_BASE_URL}/api/languages/delete/${lang_id}`,
  
  DOMAINS: `${API_BASE_URL}/api/domains`,
  DOMAIN_BY_ID: (domain_id: number) => `${API_BASE_URL}/api/domains/${domain_id}`,
  DOMAIN_CREATE: `${API_BASE_URL}/api/domains/create`,
  DOMAIN_UPDATE: (domain_id: number) => `${API_BASE_URL}/api/domains/update/${domain_id}`,
  DOMAIN_DELETE: (domain_id: number) => `${API_BASE_URL}/api/domains/delete/${domain_id}`,
  
  STRATEGIES: `${API_BASE_URL}/api/strategies/all`,
  STRATEGY_BY_ID: (strategy_id: number) => `${API_BASE_URL}/api/strategies/${strategy_id}`,
  STRATEGY_CREATE: `${API_BASE_URL}/api/strategies/create`,
  STRATEGY_UPDATE: (strategy_id: number) => `${API_BASE_URL}/api/strategies/update/${strategy_id}`,
  STRATEGY_DELETE: (strategy_id: number) => `${API_BASE_URL}/api/strategies/delete/${strategy_id}`,
};

