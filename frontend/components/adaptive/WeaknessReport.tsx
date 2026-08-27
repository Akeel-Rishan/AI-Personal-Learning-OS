"use client";

import { useState } from "react";
import type { KnowledgeGap } from "@/lib/adaptive";
import { acknowledgeGap } from "@/lib/adaptive";
import { GapInterventionModal } from "./GapInterventionModal";
import { InterventionCard } from "./InterventionCard";

export function WeaknessReport({ gaps, onChange }: { gaps: KnowledgeGap[]; onChange: () => void }): JSX.Element {
  const [selected, setSelected] = useState<KnowledgeGap | null>(null);
  async function acknowledge(gap: KnowledgeGap): Promise<void> { await acknowledgeGap(gap.id); setSelected(null); onChange(); }
  return <section><div className="flex items-end justify-between gap-4"><div><h2 className="text-xl font-bold">Active knowledge gaps</h2><p className="mt-1 text-sm text-slate-400">Targeted from your recent answers and mastery trends.</p></div><span className="text-sm text-slate-500">{gaps.length} active</span></div>{gaps.length === 0 ? <div className="mt-5 rounded-2xl border border-emerald-400/20 bg-emerald-400/5 p-8 text-center"><p className="text-2xl">✓</p><h3 className="mt-2 font-bold text-emerald-200">No active gaps detected</h3><p className="mt-1 text-sm text-slate-400">Keep learning—your next scan will check again.</p></div> : <div className="mt-5 grid gap-4 lg:grid-cols-2">{gaps.map((gap) => <InterventionCard key={gap.id} gap={gap} onOpen={setSelected} />)}</div>}<GapInterventionModal gap={selected} onClose={() => setSelected(null)} onAcknowledge={(gap) => void acknowledge(gap)} /></section>;
}
