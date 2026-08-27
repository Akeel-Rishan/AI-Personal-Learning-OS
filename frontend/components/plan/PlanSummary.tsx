import type { PlanSummary as Summary } from "@/lib/plans";

export function PlanSummary({ summary }: { summary: Summary }): JSX.Element {
  return <section className="rounded-2xl border border-emerald-400/20 bg-emerald-400/5 p-6"><h2 className="text-xl font-bold">Today at a glance</h2><p className="mt-2 text-slate-400">{summary.completion_message}</p><div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">{[[`${summary.completed_items}/${summary.total_items}`, "Tasks"], [`${summary.actual_minutes_spent}m`, "Studied"], [`+${summary.xp_earned}`, "XP"], [`${summary.streak_days} days`, "Streak"]].map(([value, label]) => <div key={label} className="rounded-xl bg-slate-950/50 p-3"><b>{value}</b><p className="mt-1 text-xs text-slate-500">{label}</p></div>)}</div></section>;
}
