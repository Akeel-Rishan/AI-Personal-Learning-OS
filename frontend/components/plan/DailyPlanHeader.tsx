import type { DailyPlan } from "@/lib/plans";

function duration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  return hours ? `${hours}h ${remaining ? `${remaining}m` : ""}`.trim() : `${remaining}m`;
}

export function DailyPlanHeader({ plan, streak }: { plan: DailyPlan; streak: number }): JSX.Element {
  const circumference = 2 * Math.PI * 46;
  const offset = circumference * (1 - plan.completion_percentage / 100);
  const formatted = new Intl.DateTimeFormat(undefined, { weekday: "long", month: "short", day: "numeric" }).format(new Date(`${plan.plan_date}T00:00:00`));
  return <header className="rounded-2xl border border-sky-400/20 bg-gradient-to-br from-sky-400/10 via-slate-900/70 to-indigo-400/10 p-6 sm:p-8"><div className="flex flex-col justify-between gap-7 md:flex-row md:items-center"><div className="max-w-3xl"><p className="text-sm font-bold uppercase tracking-[0.2em] text-sky-300">Today&apos;s Plan</p><h1 className="mt-2 text-3xl font-bold sm:text-4xl">{formatted}</h1>{plan.ai_generated_note && <p className="mt-4 max-w-2xl italic leading-7 text-slate-300">“{plan.ai_generated_note}”</p>}<div className="mt-6 grid grid-cols-3 gap-3">{[[`${plan.completed_items_count} of ${plan.total_items_count}`, "Tasks"], [duration(plan.total_estimated_minutes), "Est. time"], [`🔥 ${streak} day${streak === 1 ? "" : "s"}`, "Streak"]].map(([value, label]) => <div key={label} className="rounded-xl border border-white/5 bg-slate-950/40 p-3"><p className="font-bold">{value}</p><p className="mt-1 text-xs text-slate-500">{label}</p></div>)}</div></div><div className="relative mx-auto h-32 w-32 shrink-0"><svg viewBox="0 0 108 108" className="h-full w-full -rotate-90"><circle cx="54" cy="54" r="46" fill="none" stroke="#1e293b" strokeWidth="9" /><circle cx="54" cy="54" r="46" fill="none" stroke={plan.completion_percentage === 100 ? "#34d399" : "#38bdf8"} strokeWidth="9" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset} className="transition-[stroke-dashoffset] duration-700" /></svg><div className="absolute inset-0 flex flex-col items-center justify-center"><b className="text-2xl">{Math.round(plan.completion_percentage)}%</b><span className="text-[10px] text-slate-500">complete</span></div></div></div></header>;
}
