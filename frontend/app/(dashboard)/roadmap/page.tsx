"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { GeneratingRoadmap } from "@/components/roadmap/GeneratingRoadmap";
import { ItemDrawer } from "@/components/roadmap/ItemDrawer";
import { RoadmapHeader } from "@/components/roadmap/RoadmapHeader";
import { RoadmapTimeline } from "@/components/roadmap/RoadmapTimeline";
import { ApiError, apiGet, apiPatch, apiPost } from "@/lib/api";
import type { GoalDetail } from "@/lib/goals";
import type { Roadmap, RoadmapItemStatus, RoadmapItemUpdate } from "@/lib/roadmaps";
import { getAdaptationHistory, getGapReport, type AdaptationEvent, type KnowledgeGap } from "@/lib/adaptive";
import { AdaptationHistory } from "@/components/adaptive/AdaptationHistory";

type PageState = "loading" | "no_goal" | "not_generated" | "generating" | "ready" | "error";

function updateLocal(roadmap: Roadmap, itemId: string, status: RoadmapItemStatus): Roadmap {
  const phases = roadmap.phases.map((phase) => {
    const items = phase.items.map((item) => item.id === itemId ? { ...item, status, completed_at: status === "completed" ? new Date().toISOString() : null } : item);
    const completed = items.filter((item) => ["completed", "skipped"].includes(item.status)).length;
    return { ...phase, items, completed_items_count: completed, progress_percentage: items.length ? completed / items.length * 100 : 0 };
  });
  const completed = phases.reduce((sum, phase) => sum + phase.completed_items_count, 0);
  return { ...roadmap, phases, completed_items: completed, overall_progress_percentage: roadmap.total_items ? completed / roadmap.total_items * 100 : 0 };
}

export default function RoadmapPage(): JSX.Element {
  const router = useRouter();
  const search = useSearchParams();
  const [state, setState] = useState<PageState>("loading");
  const [goal, setGoal] = useState<GoalDetail | null>(null);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [activeGaps, setActiveGaps] = useState<KnowledgeGap[]>([]);
  const [adaptations, setAdaptations] = useState<AdaptationEvent[]>([]);
  const expandedPhase = search.get("phase");

  useEffect(() => {
    let active = true;
    apiGet<GoalDetail>("/api/v1/goals/active").then(async (activeGoal) => {
      if (!active) return;
      setGoal(activeGoal);
      try {
        const result = await apiGet<Roadmap>(`/api/v1/roadmaps/goal/${activeGoal.id}`);
        if (active) { setRoadmap(result); setState("ready"); }
      } catch (reason) {
        if (!active) return;
        setState(reason instanceof ApiError && reason.status === 404 ? "not_generated" : "error");
      }
    }).catch((reason: unknown) => { if (active) setState(reason instanceof ApiError && reason.status === 404 ? "no_goal" : "error"); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    Promise.all([getGapReport("active"), getAdaptationHistory(8)])
      .then(([report, events]) => { setActiveGaps(report.active_gaps); setAdaptations(events); })
      .catch(() => undefined);
  }, []);

  const generate = async (): Promise<void> => {
    if (!goal) return;
    setState("generating");
    try { const result = await apiPost<Roadmap>("/api/v1/roadmaps/generate", { goal_id: goal.id }); setRoadmap(result); setState("ready"); }
    catch { setState("error"); }
  };

  const setExpanded = (id: string | null): void => {
    const params = new URLSearchParams(search.toString());
    if (id) params.set("phase", id); else params.delete("phase");
    router.replace(`/roadmap${params.size ? `?${params.toString()}` : ""}`, { scroll: false });
  };

  const changeStatus = async (itemId: string, status: RoadmapItemStatus): Promise<void> => {
    if (!roadmap) return;
    const previous = roadmap;
    setRoadmap(updateLocal(roadmap, itemId, status));
    try {
      await apiPatch<RoadmapItemUpdate>(`/api/v1/roadmaps/items/${itemId}`, { status });
      const refreshed = await apiGet<Roadmap>(`/api/v1/roadmaps/${roadmap.id}`);
      setRoadmap(refreshed); setToast(status === "completed" ? "Item completed" : status === "skipped" ? "Item skipped" : "Item reset");
      window.setTimeout(() => setToast(null), 2500);
    } catch (reason) {
      setRoadmap(previous); setToast(reason instanceof ApiError ? `${reason.message} Your change was rolled back.` : "Update failed. Your change was rolled back.");
    }
  };

  const allItems = useMemo(() => roadmap?.phases.flatMap((phase) => phase.items) ?? [], [roadmap]);
  const selectedIndex = allItems.findIndex((item) => item.id === selectedId);
  const selected = selectedIndex >= 0 ? allItems[selectedIndex] : null;

  if (state === "loading") return <div className="flex min-h-[65vh] items-center justify-center text-slate-400"><div className="text-center"><span className="mx-auto block h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-sky-400" /><p className="mt-4">Loading your roadmap...</p></div></div>;
  if (state === "generating") return <GeneratingRoadmap />;
  if (state === "no_goal") return <div className="mx-auto mt-20 max-w-xl rounded-2xl border border-slate-800 bg-slate-900/60 p-10 text-center"><h1 className="text-2xl font-bold">Set a goal first</h1><p className="mt-3 text-slate-400">Your roadmap needs a destination before it can map the journey.</p><Link href="/goal/new" className="mt-6 inline-block rounded-xl bg-sky-400 px-5 py-3 font-bold text-slate-950">Set Learning Goal</Link></div>;
  if (state === "not_generated") return <div className="mx-auto mt-20 max-w-2xl rounded-2xl border border-sky-400/20 bg-gradient-to-br from-sky-400/10 to-indigo-400/5 p-10 text-center"><div className="text-5xl">⌁</div><h1 className="mt-5 text-3xl font-bold">Your personalized path is ready to be built</h1><p className="mt-3 leading-7 text-slate-400">We&apos;ll combine {goal?.title}, your assessment profile, and the skill dependency graph into a week-by-week plan.</p><button type="button" onClick={() => void generate()} className="mt-7 rounded-xl bg-sky-400 px-6 py-3 font-bold text-slate-950">Generate Roadmap →</button></div>;
  if (state === "error" || !roadmap) return <div className="mx-auto mt-20 max-w-xl rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center"><h1 className="text-2xl font-bold">Roadmap unavailable</h1><p className="mt-3 text-slate-400">We couldn&apos;t prepare the roadmap. Check the backend and try again.</p><button type="button" onClick={() => window.location.reload()} className="mt-6 rounded-xl bg-sky-400 px-5 py-3 font-bold text-slate-950">Try again</button></div>;
  return <div className="mx-auto max-w-7xl"><RoadmapHeader roadmap={roadmap} />{activeGaps.length > 0 && <Link href="/gaps" className="mt-6 block rounded-xl border border-orange-400/25 bg-orange-400/5 p-4 text-sm text-orange-100"><b>{activeGaps.length} active learning {activeGaps.length === 1 ? "gap" : "gaps"}</b> — targeted recovery work has been added to your path. <span className="font-semibold text-orange-300">Review details →</span></Link>}{roadmap.ai_generated_summary && <p className="mx-auto mt-7 max-w-4xl text-center text-lg leading-8 text-slate-300">{roadmap.ai_generated_summary}</p>}<RoadmapTimeline roadmap={roadmap} expandedPhase={expandedPhase} onExpanded={setExpanded} onOpenItem={setSelectedId} onItemStatus={(id, value) => void changeStatus(id, value)} />{adaptations.length > 0 && <div className="mt-12"><AdaptationHistory events={adaptations} /></div>}<ItemDrawer item={selected} onClose={() => setSelectedId(null)} onStatus={(value) => selected && void changeStatus(selected.id, value)} hasPrevious={selectedIndex > 0} hasNext={selectedIndex >= 0 && selectedIndex < allItems.length - 1} onPrevious={() => setSelectedId(allItems[selectedIndex - 1]?.id ?? null)} onNext={() => setSelectedId(allItems[selectedIndex + 1]?.id ?? null)} />{toast && <div role="status" className="fixed bottom-5 right-5 z-[60] max-w-sm rounded-xl border border-slate-700 bg-slate-900 px-5 py-3 text-sm shadow-2xl">{toast}</div>}</div>;
}
