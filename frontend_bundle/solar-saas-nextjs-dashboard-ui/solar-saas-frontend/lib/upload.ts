import { API_BASE, getToken } from "./api";

async function uploadFile(path: string, file: File) {
  const token = getToken();
  const form = new FormData();
  form.append("file", file);

  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: form
  });

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

export const uploadApi = {
  generationCsv: (solarSystemId: number, file: File) =>
    uploadFile(`/upload/generation/${solarSystemId}`, file),
  gridCsv: (siteId: number, file: File) =>
    uploadFile(`/upload/grid/${siteId}`, file)
};
