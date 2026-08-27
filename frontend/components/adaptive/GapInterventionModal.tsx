"use client";

import Link from "next/link";
import type { KnowledgeGap } from "@/lib/adaptive";
import { GapSeverityBadge } from "./GapSeverityBadge";

export function GapInterventionModal({ gap, onClose, onAcknowledge }: { gap: KnowledgeGap | null; onClose: () => void; onAcknowledge: (gap: KnowledgeGap) => void }): JSX.Element | null {
  if (!gap) return null;
  const data = gap.intervention_items || {};
  const tutorId = typeof data.tutor_conversation_id === "string" ? data.tutor_conversation_id : null;
  const plan = typeof data.plan === "object" && data.plan ? data.plan as Record<string, unknown> : {};
  return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/80 p-4 backdrop-blur-sm"><button type="button" aria-label="Close intervention" onClick={onClose} className="absolute inset-0" /><section role="dialog" aria-modal="true" className="relative z-10 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl"><div className="flex items-start justify-between gap-4"><div><GapSeverityBadge severity={gap.gap_severity} /><h2 className="mt-3 text-2xl font-bold">Strengthen {gap.skill_name}</h2></div><button type="button" onClick={onClose} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800">✕</button></div><div className="mt-6 space-y-5 text-sm leading-6"><div><h3 className="font-semibold text-slate-100">What we noticed</h3><p className="mt-1 text-slate-300">{gap.misconception || gap.description}</p></div><div><h3 className="font-semibold text-slate-100">Why this matters</h3><p className="mt-1 text-slate-300">{String(plan.gap_explanation || "This concept supports the next skills in your roadmap, so reinforcing it now prevents future confusion.")}</p></div><div className="rounded-xl border border-sky-400/20 bg-sky-400/5 p-4"><h3 className="font-semibold text-sky-200">Your recovery plan</h3><p className="mt-1 text-slate-300">{String(plan.action_required || "Complete the targeted review and practice activities added to your plan.")}</p></div></div><div className="mt-7 flex flex-wrap gap-3"><Link href={tutorId ? `/tutor/${tutorId}` : "/tutor"} className="rounded-lg bg-sky-400 px-4 py-2 text-sm font-bold text-slate-950">Ask AI Tutor</Link><Link href={`/exercises/practice/${gap.skill_slug}`} className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-semibold">Start practice</Link><button type="button" onClick={() => onAcknowledge(gap)} className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:bg-slate-800">Acknowledge</button></div></section></div>;
}
