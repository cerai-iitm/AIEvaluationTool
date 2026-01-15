// API Configuration
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// API endpoints
export const API_ENDPOINTS = {
  LOGIN: `${API_BASE_URL}/login`,
  DASHBOARD: `${API_BASE_URL}/api/dashboard`,
  TEST_CASES: `${API_BASE_URL}/api/testcases`,
  TEST_CASE_BY_ID: (testcase_id: number) =>
    `${API_BASE_URL}/api/testcases/${testcase_id}`,
  TEST_CASES_UPDATE_BY_ID: (testcase_id: number) =>
    `${API_BASE_URL}/api/testcases/${testcase_id}`,
  TEST_CASE_CREATE: `${API_BASE_URL}/api/testcases/create`,
  TESTCASE_DELETE: (testcase_id: number) =>
    `${API_BASE_URL}/api/testcases/delete/${testcase_id}`,
  TESTCASES_V2: `${API_BASE_URL}/api/v2/testcases`,
  TESTCASE_BY_ID_V2: (testcase_id: number) =>
    `${API_BASE_URL}/api/v2/testcases/${testcase_id}`,
  TESTCASE_CREATE_V2: `${API_BASE_URL}/api/v2/testcases/create`,
  TESTCASE_UPDATE_V2: (testcase_id: number) =>
    `${API_BASE_URL}/api/v2/testcases/update/${testcase_id}`,
  TESTCASE_DELETE_V2: (testcase_id: number) =>
    `${API_BASE_URL}/api/v2/testcases/delete/${testcase_id}`,

  TARGETS: `${API_BASE_URL}/api/targets`,
  TARGET_TYPES: `${API_BASE_URL}/api/v2/targets/target/types`,
  TARGET_BY_ID: (target_id: number) =>
    `${API_BASE_URL}/api/targets/${target_id}`,
  TARGET_CREATE: `${API_BASE_URL}/api/targets/create`,
  TARGET_UPDATE: (target_id: number) =>
    `${API_BASE_URL}/api/targets/${target_id}`,
  TARGET_DELETE: (target_id: number) =>
    `${API_BASE_URL}/api/targets/delete/${target_id}`,

  TARGETS_V2: `${API_BASE_URL}/api/v2/targets`,
  TARGET_BY_ID_V2: (target_id: number) =>
    `${API_BASE_URL}/api/v2/targets/${target_id}`,
  TARGET_CREATE_V2: `${API_BASE_URL}/api/v2/targets/create`,
  TARGET_UPDATE_V2: (target_id: number) =>
    `${API_BASE_URL}/api/v2/targets/update/${target_id}`,
  TARGET_DELETE_V2: (target_id: number) =>
    `${API_BASE_URL}/api/v2/targets/delete/${target_id}`,

  DOMAINS_V2: `${API_BASE_URL}/api/v2/domains`,
  DOMAIN_BY_ID_V2: (domain_id: number) =>
    `${API_BASE_URL}/api/v2/domains/${domain_id}`,
  DOMAIN_CREATE_V2: `${API_BASE_URL}/api/v2/domains/create`,
  DOMAIN_UPDATE_V2: (domain_id: number) =>
    `${API_BASE_URL}/api/v2/domains/update/${domain_id}`,
  DOMAIN_DELETE_V2: (domain_id: number) =>
    `${API_BASE_URL}/api/v2/domains/delete/${domain_id}`,

  LANGUAGES_V2: `${API_BASE_URL}/api/v2/languages`,
  LANGUAGES_TABLE: `${API_BASE_URL}/api/v2/languages/table`,
  LANGUAGE_BY_ID_V2: (lang_id: number) =>
    `${API_BASE_URL}/api/v2/languages/${lang_id}`,
  LANGUAGE_CREATE_V2: `${API_BASE_URL}/api/v2/languages/create`,
  LANGUAGE_UPDATE_V2: (lang_id: number) =>
    `${API_BASE_URL}/api/v2/languages/update/${lang_id}`,
  LANGUAGE_DELETE_V2: (lang_id: number) =>
    `${API_BASE_URL}/api/v2/languages/delete/${lang_id}`,

  LLMPROMPTS_V2: `${API_BASE_URL}/api/v2/llm-prompts`,
  LLMPROMPT_BY_ID_V2: (llm_prompt_id: number) =>
    `${API_BASE_URL}/api/v2/llm-prompts/${llm_prompt_id}`,
  LLMPROMPT_CREATE_V2: `${API_BASE_URL}/api/v2/llm-prompts/create`,
  LLMPROMPT_UPDATE_V2: (llm_prompt_id: number) =>
    `${API_BASE_URL}/api/v2/llm-prompts/update/${llm_prompt_id}`,
  LLMPROMPT_DELETE_V2: (llm_prompt_id: number) =>
    `${API_BASE_URL}/api/v2/llm-prompts/delete/${llm_prompt_id}`,

  PROMPTS_V2: `${API_BASE_URL}/api/v2/prompts`,
  PROMPT_BY_ID_V2: (prompt_id: number) =>
    `${API_BASE_URL}/api/v2/prompts/${prompt_id}`,
  PROMPT_CREATE_V2: `${API_BASE_URL}/api/v2/prompts/create`,
  PROMPT_UPDATE_V2: (prompt_id: number) =>
    `${API_BASE_URL}/api/v2/prompts/update/${prompt_id}`,
  PROMPT_DELETE_V2: (prompt_id: number) =>
    `${API_BASE_URL}/api/v2/prompts/delete/${prompt_id}`,
  USER_PROMPTS_V2:`${API_BASE_URL}/api/v2/prompts/user-prompt`, // user prompt list
  SYSTEM_PROMPTS_V2:`${API_BASE_URL}/api/v2/prompts/system-prompt`, // system prompt list


  RESPONSES_V2: `${API_BASE_URL}/api/v2/responses`,
  RESPONSE_BY_ID_V2: (response_id: number) =>
    `${API_BASE_URL}/api/v2/responses/${response_id}`,
  RESPONSE_CREATE_V2: `${API_BASE_URL}/api/v2/responses/create`,
  RESPONSE_UPDATE_V2: (response_id: number) =>
    `${API_BASE_URL}/api/v2/responses/update/${response_id}`,
  RESPONSE_DELETE_V2: (response_id: number) =>
    `${API_BASE_URL}/api/v2/responses/delete/${response_id}`,

  STRATEGIES_V2: `${API_BASE_URL}/api/v2/strategies`,
  STRATEGY_BY_ID_V2: (strategy_id: number) =>
    `${API_BASE_URL}/api/v2/strategies/${strategy_id}`,
  STRATEGY_CREATE_V2: `${API_BASE_URL}/api/v2/strategies/create`,
  STRATEGY_UPDATE_V2: (strategy_id: number) =>
    `${API_BASE_URL}/api/v2/strategies/update/${strategy_id}`,
  STRATEGY_DELETE_V2: (strategy_id: number) =>
    `${API_BASE_URL}/api/v2/strategies/delete/${strategy_id}`,

  //STRATEGIES: `${API_BASE_URL}/api/strategies`,
  RESPONSES: `${API_BASE_URL}/api/responses`,
  RESPONSES_ALL: `${API_BASE_URL}/api/responses/all`,
  RESPONSE_BY_ID: (response_id: number) =>
    `${API_BASE_URL}/api/responses/${response_id}`,
  RESPONSE_CREATE: `${API_BASE_URL}/api/responses/create`,
  RESPONSE_UPDATE: (response_id: number) =>
    `${API_BASE_URL}/api/responses/update/${response_id}`,
  RESPONSE_DELETE: (response_id: number) =>
    `${API_BASE_URL}/api/responses/delete/${response_id}`,
  PROMPTS: `${API_BASE_URL}/api/prompts`,
  PROMPTS_ALL: `${API_BASE_URL}/api/prompts/all`,
  PROMPT_BY_ID: (prompt_id: number) =>
    `${API_BASE_URL}/api/prompts/${prompt_id}`,
  PROMPT_CREATE: `${API_BASE_URL}/api/prompts/create`,
  PROMPT_UPDATE: (prompt_id: number) =>
    `${API_BASE_URL}/api/prompts/update/${prompt_id}`,
  PROMPT_DELETE: (prompt_id: number) =>
    `${API_BASE_URL}/api/prompts/delete/${prompt_id}`,
  LLM_PROMPTS: `${API_BASE_URL}/api/llmPrompts`,

  LLM_PROMPTS_ALL: `${API_BASE_URL}/api/llmPrompts/all`,
  LLM_PROMPT_BY_ID: (llmPrompt_id: number) =>
    `${API_BASE_URL}/api/llmPrompts/${llmPrompt_id}`,
  LLM_PROMPT_CREATE: `${API_BASE_URL}/api/llmPrompts/create`,
  LLM_PROMPT_UPDATE: (llmPrompt_id: number) =>
    `${API_BASE_URL}/api/llmPrompts/update/${llmPrompt_id}`,
  LLM_PROMPT_DELETE: (llmPrompt_id: number) =>
    `${API_BASE_URL}/api/llmPrompts/delete/${llmPrompt_id}`,

  CURRENT_USER: `${API_BASE_URL}/api/users/me`,
  USERS: `${API_BASE_URL}/api/users`,
  USER_ACTIVITY: (username: string) => `${API_BASE_URL}/api/users/${username}`,
  USER_UPDATE: (user_id: string) => `${API_BASE_URL}/api/users/${user_id}`,
  USER_DELETE: (user_id: string) => `${API_BASE_URL}/api/users/${user_id}`,
  USER_ACTIVITY_DELETE: (user_id: string) => `${API_BASE_URL}/api/users/activity/${user_id}`,
  ENTITY_ACTIVITY: (entityType: string) =>
    `${API_BASE_URL}/api/users/activity/${entityType}`,

  LANGUAGES: `${API_BASE_URL}/api/languages`,
  LANGUAGE_BY_ID: (lang_id: number) =>
    `${API_BASE_URL}/api/languages/${lang_id}`,
  LANGUAGE_CREATE: `${API_BASE_URL}/api/languages/create`,
  LANGUAGE_UPDATE: (lang_id: number) =>
    `${API_BASE_URL}/api/languages/update/${lang_id}`,
  LANGUAGE_DELETE: (lang_id: number) =>
    `${API_BASE_URL}/api/languages/delete/${lang_id}`,

  DOMAINS: `${API_BASE_URL}/api/domains`,
  DOMAIN_BY_ID: (domain_id: number) =>
    `${API_BASE_URL}/api/domains/${domain_id}`,
  DOMAIN_CREATE: `${API_BASE_URL}/api/domains/create`,
  DOMAIN_UPDATE: (domain_id: number) =>
    `${API_BASE_URL}/api/domains/update/${domain_id}`,
  DOMAIN_DELETE: (domain_id: number) =>
    `${API_BASE_URL}/api/domains/delete/${domain_id}`,

  STRATEGIES: `${API_BASE_URL}/api/strategies/all`,
  STRATEGY_BY_ID: (strategy_id: number) =>
    `${API_BASE_URL}/api/strategies/${strategy_id}`,
  STRATEGY_CREATE: `${API_BASE_URL}/api/strategies/create`,
  STRATEGY_UPDATE: (strategy_id: number) =>
    `${API_BASE_URL}/api/strategies/update/${strategy_id}`,
  STRATEGY_DELETE: (strategy_id: number) =>
    `${API_BASE_URL}/api/strategies/delete/${strategy_id}`,


  METERICS: `${API_BASE_URL}/api/v2/metrics`,
};


