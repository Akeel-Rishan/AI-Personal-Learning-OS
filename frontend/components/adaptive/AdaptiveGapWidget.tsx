"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { getGapReport, type KnowledgeGap } from "@/lib/adaptive";
import { GapSeverityBadge } from "./GapSeverityBadge";

export function AdaptiveGapWidget(): JSX.Element | null {
  const [gaps, setGaps] = useState<KnowledgeGap[]>([]);
  useEffect(() => { let active = true; getGapReport("active").then((report) => { if (active) setGaps(report.active_gaps.slice(0, 3)); }).catch(() => undefined); return () => { active = false; }; }, []);
  if (!gaps.length) return null;
  return <section className="rounded-2xl border border-orange-400/20 bg-orange-400/5 p-6"><div className="flex items-center justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-orange-300">Adaptive interventions</p><h2 className="mt-2 text-xl font-bold">Areas being strengthened</h2></div><Link href="/gaps" className="text-sm font-semibold text-orange-300">View report →</Link></div><div className="mt-5 grid gap-3 md:grid-cols-3">{gaps.map((gap) => <Link key={gap.id} href="/gaps" className="rounded-xl border border-slate-800 bg-slate-950/40 p-4 hover:border-orange-400/30"><div className="flex items-center justify-between gap-2"><b className="truncate">{gap.skill_name}</b><GapSeverityBadge severity={gap.gap_severity} /></div><p className="mt-2 text-xs text-slate-400">Mastery {gap.current_mastery_percentage}% · {gap.days_active}d active</p></Link>)}</div></section>;
}
