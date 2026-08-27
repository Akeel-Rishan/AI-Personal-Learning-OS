"use client";

import { useEffect, useState } from "react";
import { PhaseCard } from "@/components/roadmap/PhaseCard";
import type { Roadmap, RoadmapItemStatus } from "@/lib/roadmaps";

const WINDOW_SIZE = 10;

export function RoadmapTimeline({ roadmap, expandedPhase, onExpanded, onOpenItem, onItemStatus }: { roadmap: Roadmap; expandedPhase: string | null; onExpanded: (id: string | null) => void; onOpenItem: (id: string) => void; onItemStatus: (itemId: string, status: RoadmapItemStatus) => void }): JSX.Element {
  const expandedIndex = roadmap.phases.findIndex((phase) => phase.id === expandedPhase);
  const [windowStart, setWindowStart] = useState(() => expandedIndex >= 0 ? Math.floor(expandedIndex / WINDOW_SIZE) * WINDOW_SIZE : 0);
  useEffect(() => { if (expandedIndex >= 0 && (expandedIndex < windowStart || expandedIndex >= windowStart + WINDOW_SIZE)) setWindowStart(Math.floor(expandedIndex / WINDOW_SIZE) * WINDOW_SIZE); }, [expandedIndex, windowStart]);
  const phases = roadmap.phases.length > WINDOW_SIZE ? roadmap.phases.slice(windowStart, windowStart + WINDOW_SIZE) : roadmap.phases;
  return <section className="relative mt-8"><div className="absolute bottom-5 left-[19px] top-5 w-px bg-slate-800 sm:left-[27px]" />{phases.map((phase) => <div key={phase.id} className="relative mb-6 pl-12 sm:pl-16"><span className={`absolute left-1 top-7 z-10 flex h-8 w-8 items-center justify-center rounded-full border text-xs sm:left-3 ${phase.status === "completed" ? "border-emerald-400 bg-emerald-400 font-bold text-slate-950" : phase.status === "active" ? "animate-pulse border-sky-400 bg-sky-400 text-slate-950" : "border-slate-700 bg-slate-900 text-slate-500"}`}>{phase.status === "completed" ? "✓" : phase.status === "active" ? "●" : "⌕"}</span><PhaseCard phase={phase} expanded={expandedPhase === phase.id} onToggle={() => onExpanded(expandedPhase === phase.id ? null : phase.id)} onOpenItem={onOpenItem} onItemStatus={onItemStatus} /></div>)}{roadmap.phases.length > WINDOW_SIZE && <nav className="ml-12 flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/50 p-3 sm:ml-16" aria-label="Roadmap phase window"><button type="button" disabled={windowStart === 0} onClick={() => setWindowStart(Math.max(0, windowStart - WINDOW_SIZE))} className="text-sm font-semibold text-sky-300 disabled:text-slate-600">← Previous phases</button><span className="text-xs text-slate-500">Showing {windowStart + 1}–{Math.min(roadmap.phases.length, windowStart + WINDOW_SIZE)} of {roadmap.phases.length}</span><button type="button" disabled={windowStart + WINDOW_SIZE >= roadmap.phases.length} onClick={() => setWindowStart(windowStart + WINDOW_SIZE)} className="text-sm font-semibold text-sky-300 disabled:text-slate-600">Next phases →</button></nav>}</section>;
}
