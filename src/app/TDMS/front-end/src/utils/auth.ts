// Auth utilities for managing tokens
import { AUTH_LOGOUT_URL, AUTH_PAGE_URL } from "@/config/api";

export const AUTH_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_NAME: 'user_name',
  ROLE: 'role'
};

const SHARED_LOGOUT_COOKIE = "cerai_logout_at";

export const getStoredTokens = () => ({
  accessToken: localStorage.getItem(AUTH_KEYS.ACCESS_TOKEN),
  refreshToken: localStorage.getItem(AUTH_KEYS.REFRESH_TOKEN),
  userName: localStorage.getItem(AUTH_KEYS.USER_NAME),
  role: localStorage.getItem(AUTH_KEYS.ROLE),
});

export const setStoredTokens = (tokens: {
  access_token: string;
  refresh_token: string;
  user_name: string;
  role: string;
}) => {
  localStorage.setItem(AUTH_KEYS.ACCESS_TOKEN, tokens.access_token);
  localStorage.setItem(AUTH_KEYS.REFRESH_TOKEN, tokens.refresh_token);
  localStorage.setItem(AUTH_KEYS.USER_NAME, tokens.user_name);
  localStorage.setItem(AUTH_KEYS.ROLE, tokens.role);
};

export const clearStoredTokens = () => {
  localStorage.removeItem(AUTH_KEYS.ACCESS_TOKEN);
  localStorage.removeItem(AUTH_KEYS.REFRESH_TOKEN);
  localStorage.removeItem(AUTH_KEYS.USER_NAME);
  localStorage.removeItem(AUTH_KEYS.ROLE);
};

export const markSharedLogout = (): void => {
  document.cookie = `${SHARED_LOGOUT_COOKIE}=${Date.now()}; path=/; max-age=120; SameSite=Lax`;
};

export const clearSharedLogout = (): void => {
  document.cookie = `${SHARED_LOGOUT_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
};

export const hasSharedLogoutSignal = (): boolean =>
  document.cookie.split("; ").some((cookie) => cookie.startsWith(`${SHARED_LOGOUT_COOKIE}=`));

export const isAuthenticated = () => !!localStorage.getItem(AUTH_KEYS.ACCESS_TOKEN);

export const getTdmsReturnUrl = (): string => {
  const appBase = import.meta.env.BASE_URL.replace(/\/$/, "");
  return `${window.location.origin}${appBase}/dashboard`;
};

export const getLoginUrl = (returnUrl = getTdmsReturnUrl()): string =>
  `${AUTH_PAGE_URL}?return_url=${encodeURIComponent(returnUrl)}`;
  // `${AUTH_PAGE_URL}`;

export const redirectToLogin = (returnUrl?: string): void => {
  clearStoredTokens();
  window.location.replace(getLoginUrl(returnUrl));
};

export const logoutAndRedirect = (): void => {
  markSharedLogout();
  clearStoredTokens();
  const returnUrl = encodeURIComponent(AUTH_PAGE_URL);
  window.location.replace(`${AUTH_LOGOUT_URL}?return_url=${returnUrl}`);
};

const decodeJwtPayload = (token: string): Record<string, unknown> | null => {
  const [, payload] = token.split(".");
  if (!payload) return null;

  try {
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(normalized.length + ((4 - normalized.length % 4) % 4), "=");
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
};

const isTokenExpired = (token: string, skewSeconds = 30): boolean => {
  const payload = decodeJwtPayload(token);
  const exp = typeof payload?.exp === "number" ? payload.exp : null;

  if (!exp) {
    return true;
  }

  const now = Math.floor(Date.now() / 1000);
  return exp <= now + skewSeconds;
};

const storeTokensFromParams = (params: URLSearchParams): boolean => {
  const values = Object.fromEntries(params);

  if (values.access_token && values.refresh_token) {
    clearSharedLogout();
    setStoredTokens({
      access_token: values.access_token,
      refresh_token: values.refresh_token,
      user_name: values.user_name || '',
      role: values.role || '',
    });
    window.history.replaceState({}, document.title, window.location.pathname + window.location.search);
    return true;
  }

  return false;
};

export const parseUrlHashTokens = (): null => {
  const hash = window.location.hash.replace(/^#/, '');
  if (!hash) return null;
  storeTokensFromParams(new URLSearchParams(hash));
  return null;
};

export const parseUrlTokens = (): null => {
  const hash = window.location.hash.replace(/^#/, '');
  if (hash && storeTokensFromParams(new URLSearchParams(hash))) {
    return null;
  }

  const search = window.location.search.replace(/^\?/, '');
  if (search) {
    storeTokensFromParams(new URLSearchParams(search));
  }

  return null;
};

export const refreshAccessToken = async (refreshUrl: string): Promise<boolean> => {
  const refreshToken = localStorage.getItem(AUTH_KEYS.REFRESH_TOKEN);
  if (!refreshToken) return false;

  try {
    const response = await fetch(refreshUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      if (data.access_token) {
        localStorage.setItem(AUTH_KEYS.ACCESS_TOKEN, data.access_token);
      }
      return true;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }

  return false;
};

export const getValidAccessToken = async (refreshUrl: string): Promise<string | null> => {
  parseUrlTokens();

  const existingToken = localStorage.getItem(AUTH_KEYS.ACCESS_TOKEN);
  if (existingToken && !isTokenExpired(existingToken)) {
    return existingToken;
  }

  const refreshed = await refreshAccessToken(refreshUrl);
  if (!refreshed) {
    return null;
  }

  return localStorage.getItem(AUTH_KEYS.ACCESS_TOKEN);
};
