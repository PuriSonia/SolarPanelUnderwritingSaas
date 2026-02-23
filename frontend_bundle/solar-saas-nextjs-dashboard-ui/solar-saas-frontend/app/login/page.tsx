"use client";

import { useState } from "react";
import { api, setToken } from "@/lib/api";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl bg-white border border-zinc-200 shadow-sm p-6">
        <h1 className="text-xl font-semibold">Log in</h1>
        <p className="text-sm text-zinc-600 mt-1">
          Use the same email you registered with.
        </p>

        <div className="mt-5 space-y-3">
          <label className="block">
            <div className="text-xs font-medium text-zinc-600 mb-1">Email</div>
            <input
              className="w-full rounded-xl border border-zinc-200 px-3 py-2 outline-none focus:ring-2 focus:ring-zinc-200"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
            />
          </label>

          <label className="block">
            <div className="text-xs font-medium text-zinc-600 mb-1">Password</div>
            <input
              type="password"
              className="w-full rounded-xl border border-zinc-200 px-3 py-2 outline-none focus:ring-2 focus:ring-zinc-200"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </label>

          {err && <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">{err}</div>}

          <button
            className="w-full rounded-xl bg-zinc-900 text-white py-2.5 text-sm font-medium hover:bg-zinc-800 disabled:opacity-50"
            disabled={loading}
            onClick={async () => {
              setErr(null);
              setLoading(true);
              try {
                const res = await api.login(email, password);
                setToken(res.access_token);
                router.push("/dashboard");
              } catch (e: any) {
                setErr(e.message || "Login failed");
              } finally {
                setLoading(false);
              }
            }}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>

          <p className="text-sm text-zinc-600">
            No account yet?{" "}
            <Link href="/register" className="font-medium">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
