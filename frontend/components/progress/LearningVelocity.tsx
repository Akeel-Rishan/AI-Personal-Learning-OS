import type { LearningVelocity as Velocity } from "@/lib/progress";

export function LearningVelocity({ data }: { data: Velocity }): JSX.Element {
  const arrow = data.velocity_trend === "increasing" ? "↗" : data.velocity_trend === "decreasing" ? "↘" : "→";
  const tone = data.velocity_trend === "increasing" ? "text-emerald-300" : data.velocity_trend === "decreasing" ? "text-amber-300" : "text-sky-300";
  return <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
    <div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-wider text-sky-300">Learning velocity</p><h2 className="mt-2 text-xl font-bold">Your last 30 days</h2></div><span className={`text-3xl ${tone}`} title={`${data.velocity_vs_last_period}% versus previous period`}>{arrow}</span></div>
    <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">{[
      [data.mastery_gained_this_period.toFixed(2), "Mastery gained"], [data.active_days_this_period, "Active days"], [data.exercises_per_day.toFixed(1), "Exercises/day"], [`${data.minutes_per_day.toFixed(0)}m`, "Minutes/day"],
    ].map(([value, label]) => <div key={label} className="rounded-xl bg-slate-950/60 p-3"><p className="text-xl font-bold">{value}</p><p className="mt-1 text-xs text-slate-500">{label}</p></div>)}</div>
    <p className="mt-4 text-sm text-slate-400">{data.estimated_goal_completion_weeks === null ? "Keep learning to unlock a completion forecast." : `At this pace, your goal is about ${data.estimated_goal_completion_weeks} weeks away.`}</p>
  </section>;
}
