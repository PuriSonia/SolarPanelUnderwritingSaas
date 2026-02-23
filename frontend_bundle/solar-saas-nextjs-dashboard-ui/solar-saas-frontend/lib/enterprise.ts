import { API_BASE, getToken } from "./api";

async function call(path: string) {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  if (!res.ok) throw new Error("API error");
  return res.json();
}

export const enterpriseApi = {
  siteScorecard: (siteId: number, year: number) =>
    call(`/esg-reports/site/${siteId}/scorecard?year=${year}`),

  forecast: (siteId: number) =>
    call(`/forecast/demo`) // replace with real site endpoint if wired
};
