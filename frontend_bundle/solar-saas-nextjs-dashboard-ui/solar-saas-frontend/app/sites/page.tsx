"use client";

import { useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { TopNav } from "@/components/TopNav";
import { Card } from "@/components/Card";
import { api } from "@/lib/api";
import Link from "next/link";

type Site = { id: number; name: string; location?: string | null };

export default function SitesPage() {
  const [sites, setSites] = useState<Site[]>([]);
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function refresh() {
    const s = await api.listSites();
    setSites(s);
  }

  useEffect(() => {
    refresh().catch((e: any) => setErr(e.message || "Failed to load sites"));
  }, []);

  return (
    <RequireAuth>
      <TopNav />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <h1 className="text-2xl font-semibold">Sites</h1>
        <p className="text-sm text-zinc-600 mt-1">Create and manage commercial facilities.</p>

        {err && <div className="mt-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">{err}</div>}

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card title="Create site">
            <div className="space-y-3">
              <label className="block">
                <div className="text-xs font-medium text-zinc-600 mb-1">Name</div>
                <input
                  className="w-full rounded-xl border border-zinc-200 px-3 py-2 outline-none focus:ring-2 focus:ring-zinc-200"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Factory - Pune"
                />
              </label>
              <label className="block">
                <div className="text-xs font-medium text-zinc-600 mb-1">Location</div>
                <input
                  className="w-full rounded-xl border border-zinc-200 px-3 py-2 outline-none focus:ring-2 focus:ring-zinc-200"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Pune, MH"
                />
              </label>
              <button
                className="w-full rounded-xl bg-zinc-900 text-white py-2.5 text-sm font-medium hover:bg-zinc-800 disabled:opacity-50"
                disabled={saving || !name.trim()}
                onClick={async () => {
                  setErr(null);
                  setSaving(true);
                  try {
                    await api.createSite(name.trim(), location.trim() || undefined);
                    setName("");
                    setLocation("");
                    await refresh();
                  } catch (e: any) {
                    setErr(e.message || "Create failed");
                  } finally {
                    setSaving(false);
                  }
                }}
              >
                {saving ? "Creating..." : "Create"}
              </button>
              <div className="text-xs text-zinc-500">Requires admin/manager role.</div>
            </div>
          </Card>

          <div className="md:col-span-2">
            <Card title="All sites">
              {sites.length === 0 ? (
                <div className="text-sm text-zinc-600">No sites yet.</div>
              ) : (
                <div className="divide-y divide-zinc-100">
                  {sites.map((s) => (
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
        </div>
      </main>
    </RequireAuth>
  );
}
