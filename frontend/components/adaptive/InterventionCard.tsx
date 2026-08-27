import Link from "next/link";
import type { KnowledgeGap } from "@/lib/adaptive";
import { GapSeverityBadge } from "./GapSeverityBadge";

export function InterventionCard({ gap, onOpen }: { gap: KnowledgeGap; onOpen: (gap: KnowledgeGap) => void }): JSX.Element {
  const delta = gap.current_mastery_percentage - gap.mastery_percentage_at_detection;
  return <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg shadow-black/10">
    <div className="flex items-start justify-between gap-3"><div><p className="text-xs uppercase tracking-wider text-slate-500">{gap.gap_type.replaceAll("_", " ")}</p><h3 className="mt-1 text-lg font-bold">{gap.skill_name}</h3></div><GapSeverityBadge severity={gap.gap_severity} /></div>
    <p className="mt-4 text-sm leading-6 text-slate-300">{gap.misconception || gap.description}</p>
    <div className="mt-4"><div className="flex justify-between text-xs text-slate-400"><span>Mastery when detected: {gap.mastery_percentage_at_detection}%</span><span className={delta >= 0 ? "text-emerald-300" : "text-red-300"}>{delta >= 0 ? "+" : ""}{delta}%</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800"><div className="h-full rounded-full bg-gradient-to-r from-orange-400 to-sky-400" style={{ width: `${gap.current_mastery_percentage}%` }} /></div></div>
    <div className="mt-5 flex flex-wrap gap-2"><button type="button" onClick={() => onOpen(gap)} className="rounded-lg bg-sky-400 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-sky-300">View intervention</button><Link href={`/exercises/practice/${gap.skill_slug}`} className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800">Practice now</Link></div>
  </article>;
}
