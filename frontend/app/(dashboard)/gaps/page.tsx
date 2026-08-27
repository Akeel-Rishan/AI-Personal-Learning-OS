"use client";

import { useCallback, useEffect, useState } from "react";
import { AdaptationHistory } from "@/components/adaptive/AdaptationHistory";
import { WeaknessReport } from "@/components/adaptive/WeaknessReport";
import { getAdaptationHistory, getGapReport, runAdaptationScan, type AdaptationEvent, type GapReport } from "@/lib/adaptive";

export default function KnowledgeGapsPage(): JSX.Element {
  const [report, setReport] = useState<GapReport | null>(null);
  const [history, setHistory] = useState<AdaptationEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const load = useCallback(async () => { try { const [gapValue, eventValue] = await Promise.all([getGapReport("all"), getAdaptationHistory()]); setReport(gapValue); setHistory(eventValue); } finally { setLoading(false); } }, []);
  useEffect(() => { void load(); }, [load]);
  async function scan(): Promise<void> { setScanning(true); setMessage(null); try { const result = await runAdaptationScan(); setMessage(result.message); await load(); window.dispatchEvent(new Event("adaptive-learning-updated")); } catch (error) { setMessage(error instanceof Error ? error.message : "The scan could not be completed."); } finally { setScanning(false); } }
  if (loading) return <div className="grid min-h-[50vh] place-items-center text-sm text-slate-400"><span className="animate-pulse">Analyzing your learning profile…</span></div>;
  return <div className="mx-auto max-w-6xl space-y-10"><header className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-xs font-bold uppercase tracking-[.2em] text-sky-300">Adaptive learning</p><h1 className="mt-2 text-3xl font-bold">Knowledge Gap Report</h1><p className="mt-2 max-w-2xl text-slate-400">See what the system detected, why it matters, and exactly how your path changed.</p></div><button type="button" disabled={scanning} onClick={() => void scan()} className="rounded-xl bg-sky-400 px-5 py-3 text-sm font-bold text-slate-950 disabled:opacity-60">{scanning ? "Scanning…" : "Scan my progress"}</button></header>{message && <p className="rounded-xl border border-sky-400/20 bg-sky-400/5 p-3 text-sm text-sky-200">{message}</p>}{report && <><section className="grid grid-cols-2 gap-3 lg:grid-cols-4"><Stat label="Active gaps" value={report.active_gaps.length} /><Stat label="Resolved" value={report.resolved_gaps_count} /><Stat label="Total detected" value={report.total_gaps_ever} /><Stat label="Avg. resolution" value={report.average_resolution_days === null ? "—" : `${report.average_resolution_days}d`} /></section><WeaknessReport gaps={report.active_gaps} onChange={() => void load()} />{report.resolved_gaps.length > 0 && <section><h2 className="text-xl font-bold">Resolved gaps</h2><div className="mt-4 grid gap-3 sm:grid-cols-2">{report.resolved_gaps.map((gap) => <div key={gap.id} className="rounded-xl border border-emerald-400/15 bg-emerald-400/5 p-4"><p className="font-semibold text-emerald-200">✓ {gap.skill_name}</p><p className="mt-1 text-sm text-slate-400">Mastery improved to {gap.current_mastery_percentage}%</p></div>)}</div></section>}</>}<AdaptationHistory events={history} /></div>;
}

function Stat({ label, value }: { label: string; value: string | number }): JSX.Element { return <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4"><p className="text-2xl font-bold">{value}</p><p className="mt-1 text-xs text-slate-500">{label}</p></div>; }
