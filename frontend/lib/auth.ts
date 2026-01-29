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
}

export function setTenantId(tenantId: string) {
  localStorage.setItem(TENANT_KEY, tenantId);
}

export function getTenantId() {
  return localStorage.getItem(TENANT_KEY);
}
