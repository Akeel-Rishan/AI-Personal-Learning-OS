import Link from "next/link";

interface Props { hasGoal: boolean; hasAssessment: boolean; hasRoadmap: boolean; onGenerate?: () => void; }

export function EmptyPlanState({ hasGoal, hasAssessment, hasRoadmap, onGenerate }: Props): JSX.Element {
  const steps = [
    { done: hasGoal, label: "Set a learning goal", href: "/goal/new", action: "Set Goal" },
    { done: hasAssessment, label: "Complete your assessment", href: hasGoal ? "/dashboard" : "/goal/new", action: "Start Assessment" },
    { done: hasRoadmap, label: "Generate your roadmap", href: "/roadmap", action: "Generate Roadmap" },
  ];
  return <section className="mx-auto mt-12 max-w-2xl rounded-2xl border border-slate-800 bg-slate-900/60 p-7 text-center sm:p-10"><div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-sky-400/10 text-4xl">?</div><h1 className="mt-6 text-3xl font-bold">No plan for today yet</h1><p className="mt-3 text-slate-400">Complete the setup steps below and we&apos;ll time-box your next best learning activities.</p><div className="mx-auto mt-7 max-w-lg space-y-3 text-left">{steps.map((step, index) => <div key={step.label} className="flex items-center gap-4 rounded-xl border border-slate-800 bg-slate-950/40 p-4"><span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${step.done ? "bg-emerald-400 text-slate-950" : "bg-slate-800 text-slate-400"}`}>{step.done ? "✓" : index + 1}</span><span className="min-w-0 flex-1 font-semibold">{step.label}</span>{!step.done && <Link href={step.href} className="text-sm font-semibold text-sky-300">{step.action} →</Link>}</div>)}</div>{hasGoal && hasAssessment && hasRoadmap && onGenerate && <button type="button" onClick={onGenerate} className="mt-7 rounded-xl bg-sky-400 px-6 py-3 font-bold text-slate-950">Generate Today&apos;s Plan</button>}</section>;
}
