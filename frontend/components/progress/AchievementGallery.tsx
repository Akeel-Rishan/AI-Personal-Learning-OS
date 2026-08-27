"use client";
import { useState } from "react";
import type { Achievement, Achievements } from "@/lib/progress";
import { AchievementCard } from "./AchievementCard";

const filters = ["All", "Streaks", "Skills", "Projects", "Assessments", "Milestones"] as const;
function matches(achievement: Achievement, filter: typeof filters[number]): boolean { if (filter === "All") return true; const type = achievement.achievement_type.toLowerCase(); return type === filter.toLowerCase() || type === filter.toLowerCase().slice(0, -1); }
export function AchievementGallery({ data }: { data: Achievements }): JSX.Element {
  const [filter, setFilter] = useState<typeof filters[number]>("All");
  const earned = data.earned.filter(item => matches(item, filter)); const locked = data.locked.filter(item => matches(item, filter));
  return <section><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><h2 className="text-xl font-bold">Your Achievements</h2><p className="mt-1 text-sm text-slate-400">{data.total_earned} of {data.total_available} unlocked</p><div className="mt-2 h-2 w-64 max-w-full rounded bg-slate-800"><div className="h-full rounded bg-gradient-to-r from-amber-400 to-orange-400" style={{ width: `${data.completion_percentage}%` }} /></div></div><div className="flex max-w-full gap-1 overflow-x-auto rounded-xl bg-slate-900 p-1">{filters.map(item => <button key={item} type="button" onClick={() => setFilter(item)} className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm ${filter === item ? "bg-slate-700 text-white" : "text-slate-400"}`}>{item}</button>)}</div></div>
    {earned.length > 0 && <><h3 className="mt-7 text-sm font-bold uppercase tracking-wider text-emerald-300">Earned</h3><div className="mt-3 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{earned.map(item => <AchievementCard key={item.id} achievement={item} />)}</div></>}
    {locked.length > 0 && <><h3 className="mt-7 text-sm font-bold uppercase tracking-wider text-slate-500">In progress and locked</h3><div className="mt-3 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{locked.map(item => <AchievementCard key={item.id} achievement={item} />)}</div></>}
    {!earned.length && !locked.length && <p className="mt-8 text-center text-sm text-slate-500">No achievements in this category yet.</p>}
  </section>;
}
