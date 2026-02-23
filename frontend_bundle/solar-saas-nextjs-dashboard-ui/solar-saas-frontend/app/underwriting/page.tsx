"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { RequireAuth } from "@/components/RequireAuth";
import { TopNav } from "@/components/TopNav";
import { Card } from "@/components/Card";

type Run = {
  id: number;
  name?: string | null;
  created_at: string;
  model_version?: string | null;
  request_payload: any;
  results_payload: any;
};

function pct(x: any) {
  const v = Number(x);
  if (!isFinite(v)) return "—";
  return `${(v * 100).toFixed(2)}%`;
}
function bpsDelta(base: any, risk: any) {
  const b = Number(base), r = Number(risk);
  if (!isFinite(b) || !isFinite(r)) return "—";
  return `${Math.round((r - b) * 10000)} bps`;
}

export default function Underwriting MemoPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Quick-create form (minimal MVP)
  const [name, setName] = useState("Sample Carbon-Linked Project");
  const [capex, setCapex] = useState(50000000);
  const [energyRevenue, setEnergyRevenue] = useState(7000000);
  const [carbonRevenue, setCarbonRevenue] = useState(4000000);
  const [opex, setOpex] = useState(2000000);
  const [years, setYears] = useState(15);
  const [discountRate, setDiscountRate] = useState(0.1);

  // ML features must be numeric per wrapper; ship a sensible preset.
  const defaultML = useMemo(() => ({
    registry: 1,
    project_type: 2,
    afolu_activities: 0,
    methodology: 5,
    status: 1,
    country: 91,
    region: 3,
    est_annual_er: 100000,
    Crediting_Years: 10,
    ProjReg_Year: 2022
  }), []);

  const [ml, setMl] = useState<any>(defaultML);

  async function refresh() {
    setErr(null);
    try {
      const list = await api.underwritingRuns(50);
      setRuns(list);
      if (list?.length && selectedId == null) setSelectedId(list[0].id);
    } catch (e: any) {
      setErr(e.message || "Failed to load underwriting runs");
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selected = useMemo(() => runs.find(r => r.id === selectedId) || null, [runs, selectedId]);

  async function runAnalysis() {
    setLoading(true);
    setErr(null);
    try {
      const body = {
        name,
        ml_features: ml,
        financial_inputs: {
          capex,
          energy_revenue: energyRevenue,
          carbon_revenue: carbonRevenue,
          opex,
          years,
          discount_rate: discountRate
        }
      };
      const created = await api.analyzeUnderwriting Memo(body);
      await refresh();
      setSelectedId(created.id);
    } catch (e: any) {
      setErr(e.message || "Failed to run analysis");
    } finally {
      setLoading(false);
    }
  }

  async function downloadPDF(id: number) {
    try {
      const blob = await api.downloadUnderwriting MemoReport(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `underwriting_run_${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setErr(e.message || "Failed to download report");
    }
  }

  const integrity = selected?.results_payload?.integrity || {};
  const base = selected?.results_payload?.base_case || {};
  const risk = selected?.results_payload?.risk_adjusted || {};

  return (
    <RequireAuth>
      <TopNav />
      <main className="mx-auto max-w-6xl px-4 py-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Underwriting Memo</h1>
            <p className="text-sm text-zinc-600 mt-1">
              Carbon integrity risk translated into return impact (IC-ready summary).
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={runAnalysis}
              disabled={loading}
              className="rounded-lg bg-zinc-900 text-white px-3 py-2 text-xs font-semibold hover:bg-zinc-800 disabled:opacity-60 tracking-wide"
            >
              {loading ? "Running…" : "Run analysis"}
            </button>
            {selected && (
              <button
                onClick={() => downloadPDF(selected.id)}
                className="rounded-lg border border-zinc-200 px-3 py-2 text-xs font-semibold hover:bg-zinc-50 tracking-wide"
              >
                Download PDF
              </button>
            )}
          </div>
        </div>

        {err && <div className="mt-4 text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">{err}</div>}

        <div className="mt-5 flex items-center justify-between border-b border-zinc-200 pb-3">
          <div className="text-[11px] tracking-[0.18em] uppercase font-semibold text-zinc-600">Executive summary</div>
          <div className="text-xs text-zinc-500">Base vs risk-adjusted returns with integrity-based adjustments</div>
        </div>

        {/* Input strip (kept minimal) */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card title="Deal inputs">
            <div className="grid grid-cols-1 gap-3">
              <div>
                <label className="text-[11px] tracking-wide text-zinc-500">Project label</label>
                <input className="mt-1 w-full rounded-xl border border-zinc-200 px-3 py-2 text-xs" value={name} onChange={e => setName(e.target.value)} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] tracking-wide text-zinc-500">Capex</label>
                  <input className="mt-1 w-full rounded-xl border border-zinc-200 px-3 py-2 text-xs" type="number" value={capex} onChange={e => setCapex(Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-[11px] tracking-wide text-zinc-500">Years</label>
                  <input className="mt-1 w-full rounded-xl border border-zinc-200 px-3 py-2 text-xs" type="number" value={years} onChange={e => setYears(Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-[11px] tracking-wide text-zinc-500">Energy revenue / yr</label>
                  <input className="mt-1 w-full rounded-xl border border-zinc-200 px-3 py-2 text-xs" type="number" value={energyRevenue} onChange={e => setEnergyRevenue(Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-[11px] tracking-wide text-zinc-500">Opex / yr</label>
                  <input className="mt-1 w-full rounded-xl border border-zinc-200 px-3 py-2 text-xs" type="number" value={opex} onChange={e => setOpex(Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-[11px] tracking-wide text-zinc-500">Carbon revenue / yr</label>
                  <input className="mt-1 w-full rounded-xl border border-zinc-200 px-3 py-2 text-xs" type="number" value={carbonRevenue} onChange={e => setCarbonRevenue(Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-[11px] tracking-wide text-zinc-500">Discount rate</label>
                  <input className="mt-1 w-full rounded-xl border border-zinc-200 px-3 py-2 text-xs" type="number" step="0.01" value={discountRate} onChange={e => setDiscountRate(Number(e.target.value))} />
                </div>
              </div>
            </div>
          </Card>

          <Card title="Underwriting Memo register">
            <div className="text-sm text-zinc-700">
              <div className="font-medium">{selected?.name || "—"}</div>
              <div className="text-[11px] tracking-wide text-zinc-500 mt-1">
                {selected ? new Date(selected.created_at).toLocaleString() : "No runs yet"}
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-zinc-200 p-3">
                  <div className="text-[11px] tracking-wide text-zinc-500">Integrity class</div>
                  <div className="text-xl font-semibold tracking-tight">{integrity.ci_class || "—"}</div>
                </div>
                <div className="rounded-lg border border-zinc-200 p-3">
                  <div className="text-[11px] tracking-wide text-zinc-500">Issuance probability</div>
                  <div className="text-xl font-semibold tracking-tight">{pct(integrity.issuance_probability)}</div>
                </div>
                <div className="rounded-lg border border-zinc-200 p-3">
                  <div className="text-[11px] tracking-wide text-zinc-500">Base IRR</div>
                  <div className="text-xl font-semibold tracking-tight">{pct(base.irr)}</div>
                </div>
                <div className="rounded-lg border border-zinc-200 p-3">
                  <div className="text-[11px] tracking-wide text-zinc-500">Risk-adjusted IRR</div>
                  <div className="text-xl font-semibold tracking-tight">{pct(risk.irr)}</div>
                </div>
              </div>

              <div className="mt-3 rounded-lg bg-zinc-50 border border-zinc-200 p-3">
                <div className="text-[11px] tracking-wide text-zinc-500">Return impact</div>
                <div className="text-base font-semibold text-zinc-900">
                  {bpsDelta(base.irr, risk.irr)}
                </div>
                <div className="text-[11px] tracking-wide text-zinc-500 mt-1">
                  Discount rate adj.: {risk.adjusted_discount_rate != null ? (Number(risk.adjusted_discount_rate) * 100).toFixed(2) + "%" : "—"}
                </div>
              </div>

              <div className="mt-3 text-[11px] tracking-wide text-zinc-500">
                Model: {selected?.model_version || "—"} · Stored per-org for auditability.
              </div>
            </div>
          </Card>

          <Card title="Run history" right={<span className="text-[11px] tracking-wide text-zinc-500">{runs.length} runs</span>}>
            <div className="divide-y divide-zinc-100">
              {runs.length === 0 && <div className="text-sm text-zinc-600">No underwriting runs yet.</div>}
              {runs.map(r => (
                <button
                  key={r.id}
                  onClick={() => setSelectedId(r.id)}
                  className={"w-full text-left py-3 block hover:bg-zinc-50 rounded-lg px-2 " + (r.id === selectedId ? "bg-zinc-50" : "")}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-medium text-zinc-900">{r.name || `Run #${r.id}`}</div>
                      <div className="text-[11px] tracking-wide text-zinc-500">{new Date(r.created_at).toLocaleString()}</div>
                    </div>
                    <div className="text-[11px] tracking-wide text-zinc-500">#{r.id}</div>
                  </div>
                </button>
              ))}
            </div>
          </Card>
        </div>

        <div className="mt-6 text-[11px] tracking-wide text-zinc-500">
          Design note: neutral institutional styling intended for investment committee use.
        </div>
      </main>
    </RequireAuth>
  );
}
