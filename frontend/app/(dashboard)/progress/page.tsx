"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AchievementGallery } from "@/components/progress/AchievementGallery";
import { ActivityAnalytics } from "@/components/progress/ActivityAnalytics";
import { Leaderboard } from "@/components/progress/Leaderboard";
import { LearningVelocity } from "@/components/progress/LearningVelocity";
import { ProgressSummary } from "@/components/progress/ProgressSummary";
import { SkillBreakdown } from "@/components/progress/SkillBreakdown";
import { SkillMasteryChart } from "@/components/progress/SkillMasteryChart";
import { SkillRadarChart } from "@/components/progress/SkillRadarChart";
import { StreakCalendar } from "@/components/progress/StreakCalendar";
import { XPProgressBar } from "@/components/progress/XPProgressBar";
import { apiGet } from "@/lib/api";
import type { Achievements, CategoryBreakdown, HeatmapDay, LeaderboardEntry, LearningVelocity as Velocity, MasteryPoint, ProgressSummary as Summary, SkillBreakdownItem, TimeDistribution, XPHistoryDay, XPSummary } from "@/lib/progress";

type Tab = "overview" | "skills" | "activity" | "achievements";
interface PageData { summary: Summary; velocity: Velocity; categories: CategoryBreakdown[]; heatmap: HeatmapDay[]; skills: SkillBreakdownItem[]; time: TimeDistribution; xp: XPSummary; xpHistory: XPHistoryDay[]; achievements: Achievements; history: MasteryPoint[]; leaderboard: LeaderboardEntry[] }

export default function ProgressPage(): JSX.Element {
  const searchParams = useSearchParams();
  const requested = (searchParams.get("tab") as Tab) || "overview";
  const [tab, setTab] = useState<Tab>(["overview", "skills", "activity", "achievements"].includes(requested) ? requested : "overview");
  const [range, setRange] = useState(30);
  const [data, setData] = useState<PageData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setError("");
    Promise.all([
      apiGet<Summary>("/api/v1/progress/summary"),
      apiGet<Velocity>("/api/v1/progress/velocity?period_days=14"),
      apiGet<CategoryBreakdown[]>("/api/v1/progress/categories"),
      apiGet<HeatmapDay[]>("/api/v1/progress/heatmap?weeks=26"),
      apiGet<SkillBreakdownItem[]>("/api/v1/progress/skills/breakdown"),
      apiGet<TimeDistribution>("/api/v1/progress/time-distribution?days=90"),
      apiGet<XPSummary>("/api/v1/gamification/xp"),
      apiGet<XPHistoryDay[]>("/api/v1/gamification/xp/history?days=30"),
      apiGet<Achievements>("/api/v1/gamification/achievements"),
      apiGet<MasteryPoint[]>(`/api/v1/progress/skills/history?days=${range}`),
      apiGet<LeaderboardEntry[]>("/api/v1/gamification/leaderboard"),
    ]).then(([summary, velocity, categories, heatmap, skills, time, xp, xpHistory, achievements, history, leaderboard]) => {
      if (active) setData({ summary, velocity, categories, heatmap, skills, time, xp, xpHistory, achievements, history, leaderboard });
    }).catch(() => { if (active) setError("Progress data could not be loaded. Make sure the backend is running."); });
    return () => { active = false; };
  }, [range]);

  const changeTab = (next: Tab): void => { setTab(next); window.history.replaceState(null, "", `/progress?tab=${next}`); };
  if (!data && !error) return <div className="mx-auto max-w-7xl animate-pulse space-y-6"><div className="h-10 w-72 rounded bg-slate-800" /><div className="grid grid-cols-2 gap-4 lg:grid-cols-6">{Array.from({ length: 6 }, (_, index) => <div key={index} className="h-28 rounded-2xl bg-slate-900" />)}</div><div className="h-80 rounded-2xl bg-slate-900" /></div>;

  return <div className="mx-auto max-w-7xl">
    <p className="text-sm font-medium text-sky-400">Analytics and rewards</p><h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Your Progress</h1><p className="mt-2 text-slate-400">See what is improving, where to focus, and what you have unlocked.</p>
    {error && <p className="mt-6 rounded-xl border border-red-400/20 bg-red-400/5 p-4 text-red-200">{error}</p>}
    {data && <><div className="mt-7 flex gap-1 overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/70 p-1">{(["overview", "skills", "activity", "achievements"] as Tab[]).map(item => <button key={item} type="button" onClick={() => changeTab(item)} className={`min-w-fit rounded-lg px-5 py-2.5 text-sm font-semibold capitalize ${tab === item ? "bg-sky-400 text-slate-950" : "text-slate-400 hover:text-white"}`}>{item}</button>)}</div>
      {tab === "overview" && <div className="mt-6 space-y-6"><XPProgressBar xp={data.xp} /><ProgressSummary summary={data.summary} /><div className="grid gap-6 xl:grid-cols-2"><LearningVelocity data={data.velocity} /><SkillRadarChart categories={data.categories} /></div><StreakCalendar days={data.heatmap} /><Leaderboard entries={data.leaderboard} /></div>}
      {tab === "skills" && <div className="mt-6 space-y-6"><div className="flex justify-end gap-1">{[7, 30, 90].map(days => <button key={days} type="button" onClick={() => setRange(days)} className={`rounded-lg px-3 py-2 text-xs font-bold ${range === days ? "bg-indigo-400 text-slate-950" : "bg-slate-900 text-slate-400"}`}>{days} days</button>)}</div><SkillRadarChart categories={data.categories} /><SkillMasteryChart points={data.history} /><SkillBreakdown skills={data.skills} /></div>}
      {tab === "activity" && <div className="mt-6 space-y-6"><StreakCalendar days={data.heatmap} /><ActivityAnalytics xp={data.xpHistory} time={data.time} /></div>}
      {tab === "achievements" && <div className="mt-6"><AchievementGallery data={data.achievements} /></div>}
    </>}
  </div>;
}
