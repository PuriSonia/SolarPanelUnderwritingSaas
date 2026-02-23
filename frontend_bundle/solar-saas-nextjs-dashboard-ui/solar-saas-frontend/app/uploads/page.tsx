"use client";

import { useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { TopNav } from "@/components/TopNav";
import { Card } from "@/components/Card";
import { api, API_BASE, getToken } from "@/lib/api";
import { uploadApi } from "@/lib/upload";

type Site = { id: number; name: string; location?: string | null };
type SolarSystem = { id: number; name: string; capacity_kw: number; site_id: number };

export default function UploadsPage() {
  const [sites, setSites] = useState<Site[]>([]);
  const [siteId, setSiteId] = useState<number | null>(null);
  const [systems, setSystems] = useState<SolarSystem[]>([]);
  const [systemId, setSystemId] = useState<number | null>(null);

  const [genFile, setGenFile] = useState<File | null>(null);
  const [gridFile, setGridFile] = useState<File | null>(null);

  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const s = await api.listSites();
        setSites(s);
        if (s.length) setSiteId(s[0].id);
      } catch (e: any) {
        setErr(e.message || "Failed to load sites");
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      if (!siteId) return;
      setErr(null);
      try {
        const token = getToken();
        const res = await fetch(`${API_BASE}/solar/site/${siteId}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        if (!res.ok) {
          let detail = `HTTP ${res.status}`;
          try { detail = (await res.json())?.detail || detail; } catch {}
          throw new Error(detail);
        }
        const data = await res.json();
        setSystems(data);
        setSystemId(data.length ? data[0].id : null);
      } catch (e: any) {
        setErr(e.message || "Failed to load solar systems");
      }
    })();
  }, [siteId]);

  return (
    <RequireAuth>
      <TopNav />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <h1 className="text-2xl font-semibold">Uploads</h1>
        <p className="text-sm text-zinc-600 mt-1">
          Upload CSVs for generation and grid consumption (no Swagger needed).
        </p>

        {err && <div className="mt-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">{err}</div>}
        {msg && <div className="mt-4 text-sm text-green-800 bg-green-50 border border-green-200 rounded-xl p-3">{msg}</div>}

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card title="Choose site & system">
            <div className="space-y-3">
              <label className="block">
                <div className="text-xs font-medium text-zinc-600 mb-1">Site</div>
                <select
                  className="w-full rounded-xl border border-zinc-200 px-3 py-2 bg-white"
                  value={siteId ?? ""}
                  onChange={(e) => setSiteId(Number(e.target.value))}
                >
                  {sites.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <div className="text-xs font-medium text-zinc-600 mb-1">Solar system</div>
                <select
                  className="w-full rounded-xl border border-zinc-200 px-3 py-2 bg-white"
                  value={systemId ?? ""}
                  onChange={(e) => setSystemId(Number(e.target.value))}
                  disabled={systems.length === 0}
                >
                  {systems.length === 0 ? (
                    <option value="">No systems found (create one first)</option>
                  ) : (
                    systems.map((sys) => (
                      <option key={sys.id} value={sys.id}>
                        {sys.name} ({sys.capacity_kw} kW)
                      </option>
                    ))
                  )}
                </select>
              </label>

              <div className="text-xs text-zinc-500">
                CSV formats:
                <ul className="list-disc ml-5 mt-1">
                  <li>Generation: <code>month,generation_kwh</code></li>
                  <li>Grid: <code>month,grid_kwh</code></li>
                </ul>
                Month format: <code>YYYY-MM</code>
              </div>
            </div>
          </Card>

          <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card title="Upload generation CSV">
              <div className="space-y-3">
                <input type="file" accept=".csv,text/csv" onChange={(e) => setGenFile(e.target.files?.[0] || null)} />
                <button
                  className="w-full rounded-xl bg-zinc-900 text-white py-2.5 text-sm font-medium hover:bg-zinc-800 disabled:opacity-50"
                  disabled={busy || !systemId || !genFile}
                  onClick={async () => {
                    setErr(null); setMsg(null); setBusy(true);
                    try {
                      const res = await uploadApi.generationCsv(systemId!, genFile!);
                      setMsg(`Generation uploaded. Rows: ${res.rows ?? ""}`);
                    } catch (e: any) {
                      setErr(e.message || "Upload failed");
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  {busy ? "Uploading..." : "Upload generation"}
                </button>
              </div>
            </Card>

            <Card title="Upload grid consumption CSV">
              <div className="space-y-3">
                <input type="file" accept=".csv,text/csv" onChange={(e) => setGridFile(e.target.files?.[0] || null)} />
                <button
                  className="w-full rounded-xl bg-zinc-900 text-white py-2.5 text-sm font-medium hover:bg-zinc-800 disabled:opacity-50"
                  disabled={busy || !siteId || !gridFile}
                  onClick={async () => {
                    setErr(null); setMsg(null); setBusy(true);
                    try {
                      const res = await uploadApi.gridCsv(siteId!, gridFile!);
                      setMsg(`Grid uploaded. Rows: ${res.rows ?? ""}`);
                    } catch (e: any) {
                      setErr(e.message || "Upload failed");
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  {busy ? "Uploading..." : "Upload grid"}
                </button>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </RequireAuth>
  );
}
