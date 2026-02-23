export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setToken(token: string) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

async function apiFetch(path: string, init: RequestInit = {}) {
  const token = getToken();
  const headers = new Headers(init.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      detail = data?.detail || JSON.stringify(data);
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}


async function apiFetchRaw(path: string, init: RequestInit = {}) {
  const token = getToken();
  const headers = new Headers(init.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      detail = data?.detail || JSON.stringify(data);
    } catch {}
    throw new Error(detail);
  }
  return res;
}

export const api = {
  register: (org_name: string, email: string, password: string) =>
    apiFetch("/register", {
      method: "POST",
      body: JSON.stringify({ org_name, email, password })
    }),
  login: (email: string, password: string) =>
    apiFetch("/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  portfolioSummary: () => apiFetch("/portfolio/summary"),
  listSites: () => apiFetch("/sites"),
  createSite: (name: string, location?: string) =>
    apiFetch("/sites", {
      method: "POST",
      body: JSON.stringify({ name, location })
    }),
  monthlyGeneration: (siteId: number, year: string) =>
    apiFetch(`/analytics/site/${siteId}/monthly-generation?year=${encodeURIComponent(year)}`),
  monthlyGrid: (siteId: number, year: string) =>
    apiFetch(`/analytics/site/${siteId}/monthly-grid?year=${encodeURIComponent(year)}`),
  financialSiteSummary: (siteId: number) => apiFetch(`/financial/site/${siteId}/summary`),
  scope2: (siteId: number, region = "default") =>
    apiFetch(`/esg/site/${siteId}/scope2?region=${encodeURIComponent(region)}`),
  listSolarSystems: (siteId: number) => apiFetch(`/solar/site/${siteId}`),
  createSolarSystem: (site_id: number, name: string, capacity_kw: number) =>
    apiFetch(`/solar`, { method: "POST", body: JSON.stringify({ site_id, name, capacity_kw }) }),
  underwritingRuns: (limit = 50) => apiFetch(`/underwriting/runs?limit=${limit}`),
  underwritingRun: (id: number) => apiFetch(`/underwriting/runs/${id}`),
  analyzeUnderwriting: (body: any) => apiFetch(`/underwriting/analyze`, { method: "POST", body: JSON.stringify(body) }),
  downloadUnderwritingReport: async (id: number) => {
    const res = await apiFetchRaw(`/underwriting/runs/${id}/report`);
    return res.blob();
  },
  upsertTariff: (site_id: number, rate_per_kwh: number) =>
    apiFetch(`/tariffs/upsert`, { method: "POST", body: JSON.stringify({ site_id, rate_per_kwh }) }),
mlAnomaly: (siteId: number) => apiFetch(`/ml/sites/${siteId}/anomaly`),
mlUnderperformance: (siteId: number) => apiFetch(`/ml/sites/${siteId}/underperformance`),
mlPredictions: (siteId: number, limit: number = 25) => apiFetch(`/ml/sites/${siteId}/predictions?limit=${limit}`)

};
