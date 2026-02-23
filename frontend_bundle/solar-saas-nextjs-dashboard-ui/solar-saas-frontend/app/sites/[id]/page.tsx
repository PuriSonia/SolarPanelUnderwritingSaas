"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { RequireAuth } from "@/components/RequireAuth";
import { TopNav } from "@/components/TopNav";
import { Card } from "@/components/Card";
import { SeriesChart } from "@/components/SeriesChart";
import { api } from "@/lib/api";

type SolarSystem = { id: number; name: string; capacity_kw: number; site_id: number };

function fmt(n: number) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(n || 0);
}
function money(n: number) {
  return new Intl.NumberFormat(undefined, { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n || 0);
}
function tco2(n: number) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(n || 0);
}

export default function SiteDetailPage() {
  const params = useParams<{ id: string }>();
  const siteId = Number(params.id);
  const year = String(new Date().getFullYear());

  const [gen, setGen] = useState<any>(null);
  const [grid, setGrid] = useState<any>(null);
  const [fin, setFin] = useState<any>(null);
  const [scope2, setScope2] = useState<any>(null);
  const [systems, setSystems] = useState<SolarSystem[]>([]);

  const [mlAnom, setMlAnom] = useState<any>(null);
  const [mlUnder, setMlUnder] = useState<any>(null);

  const [tariff, setTariff] = useState<string>("");
  const [sysName, setSysName] = useState<string>("");
  const [sysKw, setSysKw] = useState<string>("");

  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refreshAll() {
    const [g1, g2, f, s2, ss, a1, u1] = await Promise.all([
      api.monthlyGeneration(siteId, year),
      api.monthlyGrid(siteId, year),
      api.financialSiteSummary(siteId),
      api.scope2(siteId, "default"),
      api.listSolarSystems(siteId),
      api.mlAnomaly(siteId),
      api.mlUnderperformance(siteId)
    ]);
    setGen(g1);
    setGrid(g2);
    setFin(f);
    setScope2(s2);
    setSystems(ss);
    setMlAnom(a1);
    setMlUnder(u1);
  }

  useEffect(() => {
    (async () => {
      setErr(null);
      try {
        await refreshAll();
      } catch (e: any) {
        setErr(e.message || "Failed to load site");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [siteId, year]);

  const genSeries = useMemo(() => gen?.series || [], [gen]);
  const gridSeries = useMemo(() => grid?.series || [], [grid]);

  return (
    <RequireAuth>
      <TopNav />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">Site #{siteId}</h1>
            <p className="text-sm text-zinc-600 mt-1">Year: {year}</p>
          </div>
          <button
            className="rounded-xl border border-zinc-200 px-4 py-2 text-sm font-medium hover:bg-zinc-50"
            onClick={() => refreshAll().catch((e: any) => setErr(e.message || "Refresh failed"))}
          >
            Refresh
          </button>
        </div>

        {err && <div className="mt-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">{err}</div>}
        {msg && <div className="mt-4 text-sm text-green-800 bg-green-50 border border-green-200 rounded-xl p-3">{msg}</div>}

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card title="Solar generation (kWh)">
            <div className="text-2xl font-semibold">{fin ? fmt(fin.total_generation_kwh) : "—"}</div>
          </Card>
          <Card title="Estimated savings">
            <div className="text-2xl font-semibold">{fin ? money(fin.estimated_savings) : "—"}</div>
            <div className="text-xs text-zinc-500 mt-1">Tariff: {fin ? fin.tariff_rate_per_kwh : "—"} per kWh</div>
          </Card>
          <Card title="Scope 2 net (tCO₂e)">
            <div className="text-2xl font-semibold">{scope2 ? tco2(scope2.net_scope2_tco2e) : "—"}</div>
            <div className="text-xs text-zinc-500 mt-1">
              Gross {scope2 ? tco2(scope2.gross_scope2_tco2e) : "—"} • Avoided {scope2 ? tco2(scope2.avoided_by_solar_tco2e) : "—"}
            </div>
          </Card>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card title="Add solar system">
            <div className="space-y-3">
              <label className="block">
                <div className="text-xs font-medium text-zinc-600 mb-1">Name</div>
                <input
                  className="w-full rounded-xl border border-zinc-200 px-3 py-2 outline-none focus:ring-2 focus:ring-zinc-200"
                  value={sysName}
                  onChange={(e) => setSysName(e.target.value)}
                  placeholder="Rooftop Plant A"
                />
              </label>
              <label className="block">
                <div className="text-xs font-medium text-zinc-600 mb-1">Capacity (kW)</div>
                <input
                  className="w-full rounded-xl border border-zinc-200 px-3 py-2 outline-none focus:ring-2 focus:ring-zinc-200"
                  value={sysKw}
                  onChange={(e) => setSysKw(e.target.value)}
                  placeholder="500"
                />
              </label>
              <button
                className="w-full rounded-xl bg-zinc-900 text-white py-2.5 text-sm font-medium hover:bg-zinc-800 disabled:opacity-50"
                disabled={busy || !sysName.trim() || !sysKw.trim()}
                onClick={async () => {
                  setErr(null); setMsg(null); setBusy(true);
                  try {
                    await api.createSolarSystem(siteId, sysName.trim(), Number(sysKw));
                    setSysName(""); setSysKw("");
                    setMsg("Solar system created.");
                    await refreshAll();
                  } catch (e: any) {
                    setErr(e.message || "Create solar system failed");
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                {busy ? "Saving..." : "Create solar system"}
              </button>
              <div className="text-xs text-zinc-500">Requires admin/manager role.</div>
            </div>
          </Card>

          <Card title="Set site tariff">
            <div className="space-y-3">
              <label className="block">
                <div className="text-xs font-medium text-zinc-600 mb-1">Rate per kWh</div>
                <input
                  className="w-full rounded-xl border border-zinc-200 px-3 py-2 outline-none focus:ring-2 focus:ring-zinc-200"
                  value={tariff}
                  onChange={(e) => setTariff(e.target.value)}
                  placeholder="e.g. 8.5"
                />
              </label>
              <button
                className="w-full rounded-xl bg-zinc-900 text-white py-2.5 text-sm font-medium hover:bg-zinc-800 disabled:opacity-50"
                disabled={busy || !tariff.trim()}
                onClick={async () => {
                  setErr(null); setMsg(null); setBusy(true);
                  try {
                    await api.upsertTariff(siteId, Number(tariff));
                    setTariff("");
                    setMsg("Tariff saved.");
                    await refreshAll();
                  } catch (e: any) {
                    setErr(e.message || "Save tariff failed");
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                {busy ? "Saving..." : "Save tariff"}
              </button>
              <div className="text-xs text-zinc-500">Used in savings calculations.</div>
            </div>
          </Card>

          <Card title="Solar systems">
            {systems.length === 0 ? (
              <div className="text-sm text-zinc-600">No solar systems yet. Add one on the left.</div>
            ) : (
              <div className="divide-y divide-zinc-100">
                {systems.map((s) => (
                  <div key={s.id} className="py-2">
                    <div className="text-sm font-medium">{s.name}</div>
                    <div className="text-xs text-zinc-500">{fmt(s.capacity_kw)} kW • ID {s.id}</div>
                  </div>
                ))}
              </div>
            )}
            <div className="text-xs text-zinc-500 mt-2">
              Upload generation CSVs per system in <a href="/uploads">Uploads</a>.
            </div>
          </Card>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title="Monthly solar generation">
            <SeriesChart data={genSeries} dataKey="generation_kwh" label="kWh per month" />
          </Card>
          <Card title="Monthly grid consumption">
            <SeriesChart data={gridSeries} dataKey="grid_kwh" label="kWh per month" />
          </Card>
        </div>

        <div className="mt-6 text-xs text-zinc-500">
          Tip: After adding a solar system and tariff, go to <b>Uploads</b> to upload CSVs, then hit Refresh.
        </div>
      </main>
    </RequireAuth>
  );
}
