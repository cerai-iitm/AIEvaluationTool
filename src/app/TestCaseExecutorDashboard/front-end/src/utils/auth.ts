import { AUTH_LOGOUT_URL, AUTH_PAGE_URL } from "../config/api";

const SHARED_LOGOUT_COOKIE = "cerai_logout_at";

export const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem("access_token");
  return token
    ? {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      }
    : {
        "Content-Type": "application/json",
      };
};

export const clearSession = (): void => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user_name");
  localStorage.removeItem("role");
};

export const markSharedLogout = (): void => {
  document.cookie = `${SHARED_LOGOUT_COOKIE}=${Date.now()}; path=/; max-age=120; SameSite=Lax`;
};

export const clearSharedLogout = (): void => {
  document.cookie = `${SHARED_LOGOUT_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
};

export const hasSharedLogoutSignal = (): boolean =>
  document.cookie.split("; ").some((cookie) => cookie.startsWith(`${SHARED_LOGOUT_COOKIE}=`));

const storeTokensFromParams = (params: URLSearchParams): boolean => {
  const values = Object.fromEntries(params);

  if (values.access_token && values.refresh_token) {
    clearSharedLogout();
    localStorage.setItem("access_token", values.access_token);
    localStorage.setItem("refresh_token", values.refresh_token);
    if (values.user_name) localStorage.setItem("user_name", values.user_name);
    if (values.role) localStorage.setItem("role", values.role);
    window.history.replaceState({}, document.title, window.location.pathname);
    return true;
  }

  return false;
};

export const parseUrlTokens = (): boolean => {
  const hash = window.location.hash.replace(/^#/, "");
  if (hash && storeTokensFromParams(new URLSearchParams(hash))) {
    return true;
  }

  const search = window.location.search.replace(/^\?/, "");
  if (search && storeTokensFromParams(new URLSearchParams(search))) {
    return true;
  }

  return false;
};

export const getLoginUrl = (returnUrl?: string): string => {
  if (!returnUrl) {
    return AUTH_PAGE_URL;
  }

  const target = new URL(returnUrl, window.location.origin).toString();
  return `${AUTH_PAGE_URL}?return_url=${encodeURIComponent(target)}`;
};

export const redirectToLogin = (returnUrl?: string): void => {
  clearSession();
  window.location.replace(getLoginUrl(returnUrl));
};

export const logoutAndRedirect = (): void => {
  markSharedLogout();
  clearSession();
  const returnUrl = encodeURIComponent(AUTH_PAGE_URL);
  window.location.replace(`${AUTH_LOGOUT_URL}?return_url=${returnUrl}`);
};
