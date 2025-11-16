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
  TARGET_CREATE: `${API_BASE_URL}/api/targets/create`,
  TARGET_UPDATE: (target_id: number) => `${API_BASE_URL}/api/targets/${target_id}`,

  //STRATEGIES: `${API_BASE_URL}/api/strategies`,
  RESPONSES: `${API_BASE_URL}/api/responses`,
  RESPONSES_ALL: `${API_BASE_URL}/api/responses/all`,
  RESPONSE_BY_ID: (response_id: number) => `${API_BASE_URL}/api/responses/${response_id}`,
  RESPONSE_CREATE: `${API_BASE_URL}/api/responses/create`,
  RESPONSE_UPDATE: (response_id: number) => `${API_BASE_URL}/api/responses/update/${response_id}`,
  RESPONSE_DELETE: (response_id: number) => `${API_BASE_URL}/api/responses/delete/${response_id}`,
  PROMPTS: `${API_BASE_URL}/api/prompts`,
  PROMPTS_ALL: `${API_BASE_URL}/api/prompts/all`,
  PROMPT_BY_ID: (prompt_id: number) => `${API_BASE_URL}/api/prompts/${prompt_id}`,
  PROMPT_CREATE: `${API_BASE_URL}/api/prompts/create`,
  PROMPT_UPDATE: (prompt_id: number) => `${API_BASE_URL}/api/prompts/update/${prompt_id}`,
  PROMPT_DELETE: (prompt_id: number) => `${API_BASE_URL}/api/prompts/delete/${prompt_id}`,
  LLM_PROMPTS: `${API_BASE_URL}/api/llmPrompts`,

  LLM_PROMPTS_ALL: `${API_BASE_URL}/api/llmPrompts/all`,
  LLM_PROMPT_BY_ID: (llmPrompt_id: number) => `${API_BASE_URL}/api/llmPrompts/${llmPrompt_id}`,
  LLM_PROMPT_CREATE: `${API_BASE_URL}/api/llmPrompts/create`,
  LLM_PROMPT_UPDATE: (llmPrompt_id: number) => `${API_BASE_URL}/api/llmPrompts/update/${llmPrompt_id}`,
  LLM_PROMPT_DELETE: (llmPrompt_id: number) => `${API_BASE_URL}/api/llmPrompts/delete/${llmPrompt_id}`,
  
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

