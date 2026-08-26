"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/hooks/useAuth";

export default function AssessmentLayout({ children }: { children: React.ReactNode }): JSX.Element {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  useEffect(() => { if (!isLoading && !isAuthenticated) router.replace("/login"); }, [isAuthenticated, isLoading, router]);
  if (isLoading || !isAuthenticated) return <main className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-400"><div className="text-center"><span className="mx-auto block h-9 w-9 animate-spin rounded-full border-2 border-slate-700 border-t-sky-400" /><p className="mt-4 text-sm">Restoring your assessment...</p></div></main>;
  return <>{children}</>;
}
