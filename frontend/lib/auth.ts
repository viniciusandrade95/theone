const TOKEN_KEY = "token";
const TENANT_KEY = "tenant_id";

export function setAuthToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
  document.cookie = `token=${token}; path=/; SameSite=Lax`;
}

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TENANT_KEY);
  document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  document.cookie = "tenant_id=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
}

export function setTenantId(tenantId: string) {
  localStorage.setItem(TENANT_KEY, tenantId);
  document.cookie = `tenant_id=${encodeURIComponent(tenantId)}; path=/; SameSite=Lax`;
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
