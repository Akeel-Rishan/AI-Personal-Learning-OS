// Protected dashboard shell with collapsible navigation and account controls.
"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import { ApiError, apiGet } from "@/lib/api";
import type { GoalDetail } from "@/lib/goals";
import type { Roadmap } from "@/lib/roadmaps";

type IconName = "home" | "map" | "calendar" | "zap" | "message" | "chart";

const navigation: ReadonlyArray<{ label: string; href: string; icon: IconName }> = [
  { label: "Dashboard", href: "/dashboard", icon: "home" },
  { label: "My Roadmap", href: "/roadmap", icon: "map" },
  { label: "Daily Plan", href: "/plan", icon: "calendar" },
  { label: "Skills", href: "/skills", icon: "zap" },
  { label: "AI Tutor", href: "/tutor", icon: "message" },
  { label: "Progress", href: "/progress", icon: "chart" },
];

function NavigationIcon({ name }: { name: IconName }): JSX.Element {
  const paths: Record<IconName, React.ReactNode> = {
    home: <><path d="m3 11 9-8 9 8" /><path d="M5 10v10h14V10" /><path d="M9 20v-6h6v6" /></>,
    map: <><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3Z" /><path d="M9 3v15M15 6v15" /></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></>,
    zap: <path d="M13 2 3 14h9l-1 8 10-12h-9Z" />,
    message: <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4Z" />,
    chart: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></>,
  };
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0">{paths[name]}</svg>;
}

export default function DashboardLayout({ children }: { children: React.ReactNode }): JSX.Element {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isLoading, isAuthenticated, logout } = useAuth();
  const [isExpanded, setIsExpanded] = useState(true);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [roadmapProgress, setRoadmapProgress] = useState<number | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;
    apiGet<GoalDetail>("/api/v1/goals/active")
      .then((goal) => apiGet<Roadmap>(`/api/v1/roadmaps/goal/${goal.id}`))
      .then((roadmap) => { if (active) setRoadmapProgress(roadmap.overall_progress_percentage); })
      .catch((reason: unknown) => { if (active && !(reason instanceof ApiError && reason.status === 404)) setRoadmapProgress(null); });
    return () => { active = false; };
  }, [isAuthenticated, pathname]);

  if (isLoading || !isAuthenticated || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="text-center text-slate-400">
          <span className="mx-auto block h-9 w-9 animate-spin rounded-full border-2 border-slate-700 border-t-sky-400" />
          <p className="mt-4 text-sm">Checking your session...</p>
        </div>
      </main>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <aside className={`${isExpanded ? "w-60" : "w-16"} fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-slate-800 bg-slate-900 transition-[width] duration-200 md:flex`}>
        <div className="flex h-16 items-center justify-between border-b border-slate-800 px-4">
          {isExpanded && <Link href="/dashboard" className="truncate font-bold tracking-tight">AI Learning OS</Link>}
          <button type="button" onClick={() => setIsExpanded((value) => !value)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white" aria-label="Toggle sidebar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-5 w-5"><path d={isExpanded ? "m15 18-6-6 6-6" : "m9 18 6-6-6-6"} /></svg>
          </button>
        </div>
        <nav className="flex-1 space-y-1 p-2 pt-5">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} title={isExpanded ? undefined : item.label} className={`flex h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium transition ${isActive ? "bg-sky-400/10 text-sky-300" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}>
                <NavigationIcon name={item.icon} />
                {isExpanded && <span className="flex min-w-0 flex-1 items-center justify-between gap-2"><span>{item.label}</span>{item.href === "/roadmap" && roadmapProgress !== null && <span className="rounded-full bg-sky-400/10 px-2 py-0.5 text-[10px] text-sky-300">{Math.round(roadmapProgress)}%</span>}</span>}
              </Link>
            );
          })}
        </nav>
        {isExpanded && <Link href="/goal/new" className="mx-3 mb-3 rounded-xl bg-sky-400 px-4 py-3 text-center text-sm font-bold text-slate-950 transition hover:bg-sky-300">+ Set Learning Goal</Link>}
        {isExpanded && <p className="p-4 text-xs leading-5 text-slate-600">Your adaptive learning workspace</p>}
      </aside>

      <div className={`${isExpanded ? "md:ml-60" : "md:ml-16"} min-w-0 flex-1 transition-[margin] duration-200`}>
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-800 bg-slate-950/90 px-6 backdrop-blur">
          <div>
            <p className="text-sm font-semibold">AI Learning OS</p>
            <p className="text-xs text-slate-500">Personal learning workspace</p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/goal/new" className="hidden rounded-lg border border-sky-400/30 px-3 py-2 text-xs font-semibold text-sky-300 transition hover:bg-sky-400/10 sm:block">Set Goal</Link>
            <div className="relative">
            <button type="button" onClick={() => setIsMenuOpen((value) => !value)} className="flex items-center gap-3 rounded-lg p-1.5 pr-3 hover:bg-slate-900" aria-expanded={isMenuOpen}>
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-indigo-500 text-sm font-bold text-slate-950">{user.full_name.charAt(0).toUpperCase()}</span>
              <span className="hidden text-left sm:block"><span className="block text-sm font-medium">{user.full_name}</span><span className="block max-w-44 truncate text-xs text-slate-500">{user.email}</span></span>
              <span className="text-xs text-slate-500">▾</span>
            </button>
            {isMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 rounded-xl border border-slate-800 bg-slate-900 p-2 shadow-2xl shadow-black/30">
                <button type="button" className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-800">My Profile</button>
                <button type="button" className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-800">Settings</button>
                <div className="my-1 h-px bg-slate-800" />
                <button type="button" onClick={() => void logout()} className="w-full rounded-lg px-3 py-2 text-left text-sm text-red-300 hover:bg-red-500/10">Sign Out</button>
              </div>
            )}
            </div>
          </div>
        </header>
        <main className="p-4 sm:p-8">{children}</main>
      </div>
    </div>
  );
}
