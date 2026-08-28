// Protected dashboard shell with collapsible navigation and account controls.
"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import { ApiError, apiGet } from "@/lib/api";
import type { GoalDetail } from "@/lib/goals";
import type { Roadmap } from "@/lib/roadmaps";
import type { DailyPlan } from "@/lib/plans";
import type { Recommendation } from "@/lib/exercises";
import type { StreakInfo, XPSummary } from "@/lib/progress";
import { XPProgressBar } from "@/components/progress/XPProgressBar";
import { AchievementToast } from "@/components/gamification/AchievementToast";
import { AdaptationBanner } from "@/components/adaptive/AdaptationBanner";
import { AdaptiveGapWidget } from "@/components/adaptive/AdaptiveGapWidget";
import { getGapReport } from "@/lib/adaptive";
import { getMyProjects } from "@/lib/projects";
import { ProjectDashboardWidget } from "@/components/projects/ProjectDashboardWidget";

type IconName = "home" | "map" | "calendar" | "zap" | "project" | "message" | "chart" | "trophy" | "alert";

const navigation: ReadonlyArray<{ label: string; href: string; icon: IconName }> = [
  { label: "Dashboard", href: "/dashboard", icon: "home" },
  { label: "My Roadmap", href: "/roadmap", icon: "map" },
  { label: "Daily Plan", href: "/plan", icon: "calendar" },
  { label: "Practice", href: "/exercises", icon: "zap" },
  { label: "Projects", href: "/projects", icon: "project" },
  { label: "Knowledge Gaps", href: "/gaps", icon: "alert" },
  { label: "AI Tutor", href: "/tutor", icon: "message" },
  { label: "Progress", href: "/progress", icon: "chart" },
  { label: "Achievements", href: "/achievements", icon: "trophy" },
];

function NavigationIcon({ name }: { name: IconName }): JSX.Element {
  const paths: Record<IconName, React.ReactNode> = {
    home: <><path d="m3 11 9-8 9 8" /><path d="M5 10v10h14V10" /><path d="M9 20v-6h6v6" /></>,
    map: <><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3Z" /><path d="M9 3v15M15 6v15" /></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></>,
    zap: <path d="M13 2 3 14h9l-1 8 10-12h-9Z" />,
    project: <><path d="M4 5h16v14H4Z"/><path d="M8 5V3h8v2M8 10h8M8 14h5"/></>,
    message: <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4Z" />,
    chart: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></>,
    trophy: <><path d="M8 4h8v5a4 4 0 0 1-8 0Z"/><path d="M8 6H4v1a4 4 0 0 0 4 4M16 6h4v1a4 4 0 0 1-4 4M12 13v4M8 21h8M9 17h6"/></>,
    alert: <><path d="M12 3 2.5 20h19Z"/><path d="M12 9v5M12 17h.01"/></>,
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
  const [pendingPlanItems, setPendingPlanItems] = useState<number | null>(null);
  const [practiceWarning, setPracticeWarning] = useState(false);
  const [activeGapCount, setActiveGapCount] = useState(0);
  const [activeProjectCount, setActiveProjectCount] = useState(0);
  const [xp, setXp] = useState<XPSummary | null>(null);
  const [streakInfo, setStreakInfo] = useState<StreakInfo | null>(null);

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

  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;
    getGapReport("active").then((value) => { if (active) setActiveGapCount(value.active_gaps.length); }).catch(() => undefined);
    getMyProjects("active").then((value) => { if (active) setActiveProjectCount(value.length); }).catch(() => undefined);
    return () => { active = false; };
  }, [isAuthenticated, pathname]);

  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;
    Promise.all([
      apiGet<XPSummary>("/api/v1/gamification/xp"),
      apiGet<StreakInfo>("/api/v1/gamification/streak"),
    ]).then(([xpValue, streakValue]) => { if (active) { setXp(xpValue); setStreakInfo(streakValue); } }).catch(() => undefined);
    return () => { active = false; };
  }, [isAuthenticated, pathname]);

  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;
    apiGet<DailyPlan>("/api/v1/plans/today")
      .then((plan) => { if (active) setPendingPlanItems(plan.items.filter((item) => !["completed", "skipped"].includes(item.status)).length); })
      .catch(() => { if (active) setPendingPlanItems(null); });
    return () => { active = false; };
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;
    apiGet<Recommendation[]>("/api/v1/exercises/recommended?limit=1")
      .then((items) => { if (active) setPracticeWarning(items.some((item) => item.skill_mastery < 0.5)); })
      .catch(() => { if (active) setPracticeWarning(false); });
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
          {navigation.map((entry) => {
            const item = entry.href === "/exercises" && practiceWarning ? { ...entry, label: `${entry.label} ⚠` } : entry;
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} title={isExpanded ? undefined : item.label} className={`flex h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium transition ${isActive ? "bg-sky-400/10 text-sky-300" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}>
                <NavigationIcon name={item.icon} />
                {isExpanded && <span className="flex min-w-0 flex-1 items-center justify-between gap-2"><span>{item.label}</span>{item.href === "/roadmap" && roadmapProgress !== null && <span className="rounded-full bg-sky-400/10 px-2 py-0.5 text-[10px] text-sky-300">{Math.round(roadmapProgress)}%</span>}{item.href === "/plan" && pendingPlanItems !== null && pendingPlanItems > 0 && <span className="rounded-full bg-orange-400 px-2 py-0.5 text-[10px] font-bold text-slate-950">{pendingPlanItems}</span>}{item.href === "/projects" && activeProjectCount > 0 && <span className="rounded-full bg-indigo-400 px-2 py-0.5 text-[10px] font-bold text-slate-950">{activeProjectCount}</span>}{item.href === "/gaps" && activeGapCount > 0 && <span className="rounded-full bg-red-400 px-2 py-0.5 text-[10px] font-bold text-slate-950">{activeGapCount}</span>}{item.href === "/tutor" && <span title="Tutor online" className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,.7)]" />}</span>}
              </Link>
            );
          })}
        </nav>
        {isExpanded && xp && <div className="mx-3 mb-3"><XPProgressBar xp={xp} compact /></div>}
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
            {xp && <Link href="/progress" className="hidden items-center gap-2 rounded-lg border border-indigo-400/20 bg-indigo-400/5 px-3 py-2 text-xs sm:flex"><b className="text-indigo-300">Lv {xp.level}</b><span className="text-slate-400">{xp.total_xp} XP</span></Link>}
            {streakInfo && <Link href="/progress?tab=activity" className={`rounded-lg px-3 py-2 text-sm font-bold ${streakInfo.streak_at_risk ? "bg-amber-400/10 text-amber-300" : "text-orange-300"}`} title={streakInfo.streak_at_risk ? "Complete learning activity today to keep your streak" : "Current learning streak"}>🔥 {streakInfo.current_streak}</Link>}
            <Link href="/progress?tab=achievements" aria-label="Achievement notifications" className="rounded-lg p-2 text-slate-400 hover:bg-slate-900 hover:text-white"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg></Link>
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
        <main className="p-4 sm:p-8"><AdaptationBanner />{pathname === "/dashboard" && <div className="mx-auto mb-6 grid max-w-7xl gap-4"><AdaptiveGapWidget /><ProjectDashboardWidget /></div>}{children}</main>
      </div>
      <AchievementToast />
    </div>
  );
}
