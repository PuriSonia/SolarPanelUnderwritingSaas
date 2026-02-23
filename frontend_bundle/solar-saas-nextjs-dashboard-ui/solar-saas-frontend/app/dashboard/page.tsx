"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { RequireAuth } from "@/components/RequireAuth";
import { TopNav } from "@/components/TopNav";
import { Card } from "@/components/Card";
import Link from "next/link";

type Portfolio = {
  total_sites: number;
  total_generation_kwh: number;
  total_grid_kwh: number;
  estimated_total_savings: number;
};

type Site = { id: number; name: string; location?: string | null };

function fmt(n: number) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(n || 0);
}
function money(n: number) {
  return new Intl.NumberFormat(undefined, { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n || 0);
}

export default function DashboardPage() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [sites, setSites] = useState<Site[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setErr(null);
      try {
        const [p, s] = await Promise.all([api.portfolioSummary(), api.listSites()]);
        setPortfolio(p);
        setSites(s);
      } catch (e: any) {
        setErr(e.message || "Failed to load dashboard");
      }
    })();
  }, []);

  return (
    <RequireAuth>
      <TopNav />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">Portfolio</h1>
            <p className="text-sm text-zinc-600 mt-1">Commercial solar performance + ESG snapshot.</p>
          </div>
          <Link href="/sites" className="rounded-xl bg-zinc-900 text-white px-4 py-2 text-sm font-medium hover:bg-zinc-800 no-underline">
            Manage sites
          </Link>
        </div>

        {err && <div className="mt-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">{err}</div>}

        <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card title="Sites">
            <div className="text-2xl font-semibold">{portfolio ? fmt(portfolio.total_sites) : "—"}</div>
          </Card>
          <Card title="Solar generation (kWh)">
            <div className="text-2xl font-semibold">{portfolio ? fmt(portfolio.total_generation_kwh) : "—"}</div>
          </Card>
          <Card title="Grid consumption (kWh)">
            <div className="text-2xl font-semibold">{portfolio ? fmt(portfolio.total_grid_kwh) : "—"}</div>
          </Card>
          <Card title="Estimated savings">
            <div className="text-2xl font-semibold">{portfolio ? money(portfolio.estimated_total_savings) : "—"}</div>
            <div className="text-xs text-zinc-500 mt-1">Uses site tariffs × generation</div>
          </Card>
        </div>

        <div className="mt-6">
          <Card
            title="Sites"
            right={<Link className="text-sm font-medium" href="/sites">View all</Link>}
          >
            {sites.length === 0 ? (
              <div className="text-sm text-zinc-600">No sites yet. Create one in the Sites page.</div>
            ) : (
              <div className="divide-y divide-zinc-100">
                {sites.slice(0, 8).map((s) => (
                  <div key={s.id} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="font-medium">{s.name}</div>
                      <div className="text-xs text-zinc-500">{s.location || "—"}</div>
                    </div>
                    <Link href={`/sites/${s.id}`} className="text-sm font-medium">
                      Open
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </main>
    </RequireAuth>
  );
}
