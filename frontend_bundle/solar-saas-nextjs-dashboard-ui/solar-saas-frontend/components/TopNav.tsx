"use client";

import Link from "next/link";
import { clearToken } from "@/lib/api";
import { useRouter } from "next/navigation";

export function TopNav() {
  const router = useRouter();
  return (
    <div className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-zinc-200">
      <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
        <Link href="/dashboard" className="font-semibold text-zinc-900 no-underline">
          Solar SaaS
        </Link>
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="text-sm">Dashboard</Link>
          <Link href="/sites" className="text-sm">Sites</Link>
          <Link href="/uploads" className="text-sm">Uploads</Link>
          <Link href="/underwriting" className="text-sm">Underwriting</Link>
          <button
            className="text-sm rounded-lg border border-zinc-200 px-3 py-1.5 hover:bg-zinc-50"
            onClick={() => {
              clearToken();
              router.push("/login");
            }}
          >
            Log out
          </button>
        </div>
      </div>
    </div>
  );
}
