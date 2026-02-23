"use client";

import { useEffect } from "react";
import { getToken } from "@/lib/api";
import { useRouter } from "next/navigation";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  useEffect(() => {
    const t = getToken();
    if (!t) router.replace("/login");
  }, [router]);
  return <>{children}</>;
}
