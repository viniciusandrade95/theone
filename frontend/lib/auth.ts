const TOKEN_KEY = "token";
const TENANT_KEY = "tenant_id";
const AUTH_COOKIE_MAX_AGE_SECONDS = Number(
  process.env.NEXT_PUBLIC_AUTH_COOKIE_MAX_AGE_SECONDS ?? 60 * 60 * 24 * 7,
);

export function setAuthToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
  document.cookie = `token=${encodeURIComponent(token)}; path=/; max-age=${AUTH_COOKIE_MAX_AGE_SECONDS}; SameSite=Lax`;
}

export function getAuthToken() {
  const fromStorage = localStorage.getItem(TOKEN_KEY);
  if (fromStorage) {
    return fromStorage;
  }
  const cookieEntry = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith("token="));
  if (!cookieEntry) {
    return null;
  }
  return decodeURIComponent(cookieEntry.replace("token=", ""));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TENANT_KEY);
  document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  document.cookie = "tenant_id=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
}

export function setTenantId(tenantId: string) {
  localStorage.setItem(TENANT_KEY, tenantId);
  document.cookie = `tenant_id=${encodeURIComponent(tenantId)}; path=/; max-age=${AUTH_COOKIE_MAX_AGE_SECONDS}; SameSite=Lax`;
}

export function getTenantId() {
  const fromStorage = localStorage.getItem(TENANT_KEY);
  if (fromStorage) {
    return fromStorage;
  }
  const cookieEntry = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith("tenant_id="));
  if (!cookieEntry) {
    return null;
  }
  return decodeURIComponent(cookieEntry.replace("tenant_id=", ""));
}
