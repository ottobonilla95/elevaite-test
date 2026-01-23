// Centralized API client placeholder; add real implementation when wiring backend.
export interface ApiClientConfig {
  baseUrl?: string;
  tenantId?: string;
  apiKey?: string;
  userId?: string;
  organizationId?: string;
  projectId?: string;
  accountId?: string;
}

export interface ApiClient {
  get: <T>(path: string, init?: RequestInit) => Promise<T>;
  post: <T>(path: string, body?: unknown, init?: RequestInit) => Promise<T>;
  put: <T>(path: string, body?: unknown, init?: RequestInit) => Promise<T>;
  patch: <T>(path: string, body?: unknown, init?: RequestInit) => Promise<T>;
  del: <T>(path: string, init?: RequestInit) => Promise<T>;
  delete: <T>(path: string, init?: RequestInit) => Promise<T>;
}

export function createApiClient(config: ApiClientConfig = {}): ApiClient {
  const envBaseUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "";
  const envTenantId = "default"; //process.env.NEXT_PUBLIC_ELEVAITE_TENANT_ID;
  const envProjectId = process.env.NEXT_PUBLIC_ELEVAITE_PROJECT_ID;
  const envAccountId = process.env.NEXT_PUBLIC_ELEVAITE_ACCOUNT_ID;
  const envApiKey = process.env.ELEVAITE_API_KEY;

  const {
    baseUrl = envBaseUrl,
    tenantId = envTenantId,
    apiKey = envApiKey,
    userId = "",
    organizationId = "00000000-0000-0000-0000-000000000001",
    projectId = "00000000-0000-0000-0000-000000000001",
    accountId = "00000000-0000-0000-0000-000000000001"
  } = config;

  function withDefaults(init: RequestInit = {}): RequestInit {
    const headers: Record<string, string> = {
      ...(init.headers as Record<string, string> || {}),
    };
    if (tenantId) headers["X-Tenant-ID"] = tenantId;
    if (apiKey) headers["X-elevAIte-apikey"] = apiKey;
    if (userId) headers["X-elevAIte-UserId"] = userId;
    if (organizationId) headers["X-elevAIte-OrganizationId"] = organizationId;
    if (projectId) headers["X-elevAIte-ProjectId"] = projectId;
    if (accountId) headers["X-elevAIte-AccountId"] = accountId;
    console.log("🔐 Headers:", headers);
    return { ...init, headers };
  }

  function buildUrl(path: string): string {
    if (path.startsWith("http")) return path;
    const cleanBase = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
    const cleanPath = path.startsWith("/") ? path : `/${path}`;
    return `${cleanBase}${cleanPath}`;
  }

  async function handle<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
    console.log("📤 Request URL:", input);
    console.log("📤 Request Init:", init);
    const response = await fetch(input, withDefaults(init));
    console.log("📥 Response Status:", response.status);
    const text = await response.text();
    console.log("📥 Response Body:", text);
    if (!response.ok) throw new Error(`Request failed with status ${response.status.toString()}`);
    return JSON.parse(text) as T;
  }

  return {
    get<T>(path: string, init?: RequestInit): Promise<T> {
      return handle<T>(buildUrl(path), { method: "GET", ...init });
    },
    post<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
      return handle<T>(buildUrl(path), {
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
        headers: { "Content-Type": "application/json" },
        ...init,
      });
    },
    put<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
      return handle<T>(buildUrl(path), {
        method: "PUT",
        body: body ? JSON.stringify(body) : undefined,
        headers: { "Content-Type": "application/json" },
        ...init,
      });
    },
    patch<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
      return handle<T>(buildUrl(path), {
        method: "PATCH",
        body: body ? JSON.stringify(body) : undefined,
        headers: { "Content-Type": "application/json" },
        ...init,
      });
    },
    del<T>(path: string, init?: RequestInit): Promise<T> {
      return handle<T>(buildUrl(path), { method: "DELETE", ...init });
    },
    delete<T>(path: string, init?: RequestInit): Promise<T> {
      return handle<T>(buildUrl(path), { method: "DELETE", ...init });
    },
  };
}
