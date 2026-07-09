export const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL !;

export const AUTH_SERVICE_URL =
  process.env.REACT_APP_AUTH_SERVICE_URL || "http://localhost:7500";

export const AUTH_PAGE_URL = `${AUTH_SERVICE_URL}/web/login`;
export const LOGIN_URL = process.env.REACT_APP_LOGIN_URL || AUTH_PAGE_URL;
export const AUTH_LOGOUT_URL = `${AUTH_SERVICE_URL}/web/logout`;

 export const API_ENDPOINTS = {
    GET_ALL_FILTERS: "/get_all_filters",
    GET_ALL_TEST_RUNS: "/get_all_test_runs",
   ANALYSE_RUN: (runName: string, mode?: string) =>
    `${API_BASE_URL}/analyse/${encodeURIComponent(runName)}${
      mode ? `?mode=${mode}` : ""
    }`,
    ANALYSE_DETAILS: (runName: string, mode: string) =>
    `${API_BASE_URL}/analyse/${encodeURIComponent(runName)}/details?mode=${mode}`,
    ANALYSE_RUN_STATUS: (runName: string) =>
    `${API_BASE_URL}/analyse/${encodeURIComponent(runName)}/status`,
    DOWNLOAD_REPORT: (runName: string) =>
    `${API_BASE_URL}/test-runs/${runName}/evaluation-report`,
    GET_CONVERSATION: (conversationId: string) =>
    `${API_BASE_URL}/conversations/full/${conversationId}`,
    GET_TIMELINE: (runName: string) =>
    `${API_BASE_URL}/test-runs/${runName}/timeline`,
    GET_TEST_RUN_DETAILS: (runName: string, query: string) =>
    `${API_BASE_URL}/test-runs/${encodeURIComponent(runName)}${
      query ? `?${query}` : ""
    }`,
    DELETE_TEST_RUN: (runName: string) =>
    `${API_BASE_URL}/test-runs/${encodeURIComponent(runName)}`,
    GET_METRICS_BY_PLAN: (planName: string) =>
    `${API_BASE_URL}/get_metrics_by_plan/${planName}`,
    GET_TARGET_METADATA: (targetName: string) =>
    `${API_BASE_URL}/targets/${encodeURIComponent(targetName)}/metadata`,
    START_RUN: `${API_BASE_URL}/start-run`,
    DOWNLOAD_REPORT_NEW: (runName: string) =>
  `${API_BASE_URL}/report/${encodeURIComponent(runName)}`,
    
    CONTINUE_RUN: `${API_BASE_URL}/continue-run`,    
    DEV_Config: `${API_BASE_URL}/__dev/config`,

    ANALYSE_HEALTH: `${API_BASE_URL}/analyse/health`,
}  


export const WS_BASE_URL = API_BASE_URL.startsWith("https")
  ? API_BASE_URL.replace("https://", "wss://")
  : API_BASE_URL.replace("http://", "ws://");

export const WS_ENDPOINTS = {
  TEST_RUN: `${WS_BASE_URL}/ws/test-run`,
};
