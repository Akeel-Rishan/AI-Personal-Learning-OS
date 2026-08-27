"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CompletionCelebration } from "@/components/plan/CompletionCelebration";
import { DailyPlanHeader } from "@/components/plan/DailyPlanHeader";
import { EmptyPlanState } from "@/components/plan/EmptyPlanState";
import { PlanItemCard } from "@/components/plan/PlanItemCard";
import { PlanSummary as PlanSummaryCard } from "@/components/plan/PlanSummary";
import { ApiError, apiGet, apiPatch, apiPost } from "@/lib/api";
import type { AssessmentStatus } from "@/lib/assessments";
import type { GoalDetail } from "@/lib/goals";
import { useAuth } from "@/lib/hooks/useAuth";
import type { DailyPlan, DailyPlanItem, PlanItemStatus, PlanSummary, StreakInfo } from "@/lib/plans";
import type { Roadmap } from "@/lib/roadmaps";

interface SetupState { hasGoal: boolean; hasAssessment: boolean; hasRoadmap: boolean }

function optimisticPlan(plan: DailyPlan, itemId: string, status: PlanItemStatus): DailyPlan {
  const items = plan.items.map((item) => {
    if (status === "in_progress" && item.id !== itemId && item.status === "in_progress") return { ...item, status: "pending" as const };
    return item.id === itemId ? { ...item, status, completed_at: status === "completed" ? new Date().toISOString() : null } : item;
  });
  const completed = items.filter((item) => item.status === "completed").length;
  const allCompleted = items.length > 0 && completed === items.length;
  const allTerminal = items.every((item) => ["completed", "skipped"].includes(item.status));
  return { ...plan, items, completed_items_count: completed, completion_percentage: items.length ? completed / items.length * 100 : 0, status: allCompleted ? "completed" : allTerminal ? "partial" : items.some((item) => item.status !== "pending") ? "in_progress" : "pending" };
}

export default function PlanPage(): JSX.Element {
  const { user } = useAuth();
  const [plan, setPlan] = useState<DailyPlan | null>(null);
  const [streak, setStreak] = useState(0);
  const [summary, setSummary] = useState<PlanSummary | null>(null);
  const [showCelebration, setShowCelebration] = useState(false);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [setup, setSetup] = useState<SetupState>({ hasGoal: false, hasAssessment: false, hasRoadmap: false });
  const queue = useRef<Promise<void>>(Promise.resolve());
  const queueDepth = useRef(0);

  const diagnoseSetup = useCallback(async (): Promise<void> => {
    try {
      const goal = await apiGet<GoalDetail>("/api/v1/goals/active");
      let hasAssessment = false, hasRoadmap = false;
      try { hasAssessment = (await apiGet<AssessmentStatus>(`/api/v1/assessments/goal/${goal.id}`)).status === "completed"; } catch { hasAssessment = false; }
      try { await apiGet<Roadmap>(`/api/v1/roadmaps/goal/${goal.id}`); hasRoadmap = true; } catch { hasRoadmap = false; }
      setSetup({ hasGoal: true, hasAssessment, hasRoadmap });
    } catch { setSetup({ hasGoal: false, hasAssessment: false, hasRoadmap: false }); }
  }, []);

  const loadPlan = useCallback(async (): Promise<void> => {
    try {
      const [today, streakInfo] = await Promise.all([
        apiGet<DailyPlan>("/api/v1/plans/today"),
        apiGet<StreakInfo>("/api/v1/plans/streak"),
      ]);
      setPlan(today); setStreak(streakInfo.current_streak);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 404) await diagnoseSetup();
      else setToast(reason instanceof ApiError ? reason.message : "Today's plan could not be loaded.");
    } finally { setLoading(false); }
  }, [diagnoseSetup]);

  useEffect(() => { void loadPlan(); }, [loadPlan]);
  useEffect(() => {
    const interval = window.setInterval(() => {
      if (!plan || queueDepth.current > 0) return;
      apiGet<DailyPlan>(`/api/v1/plans/${plan.id}`).then(setPlan).catch(() => undefined);
    }, 30000);
    return () => window.clearInterval(interval);
  }, [plan]);

  const changeStatus = (item: DailyPlanItem, status: PlanItemStatus, minutes?: number): void => {
    if (!plan) return;
    const previous = plan;
    setPlan(optimisticPlan(plan, item.id, status));
    queueDepth.current += 1;
    queue.current = queue.current.then(async () => {
      try {
        await apiPatch<DailyPlanItem>(`/api/v1/plans/items/${item.id}`, { status, time_spent_minutes: minutes ?? null });
        const refreshed = await apiGet<DailyPlan>(`/api/v1/plans/${plan.id}`);
        setPlan(refreshed);
        if (refreshed.status === "completed") {
          const completion = await apiGet<PlanSummary>(`/api/v1/plans/${refreshed.id}/summary`);
          setSummary(completion); setShowCelebration(true); setStreak(completion.streak_days);
        }
      } catch (reason) {
        setPlan(previous);
        setToast(reason instanceof ApiError ? `${reason.message} Your change was rolled back.` : "Update failed. Your change was rolled back.");
      } finally { queueDepth.current -= 1; }
    });
  };

  const regenerate = async (): Promise<void> => {
    setRegenerating(true); setToast(null);
    try { setPlan(await apiPost<DailyPlan>("/api/v1/plans/generate", {})); }
    catch (reason) { setToast(reason instanceof ApiError ? reason.message : "The plan could not be regenerated."); }
    finally { setRegenerating(false); }
  };

  if (loading) return <div className="flex min-h-[65vh] items-center justify-center text-slate-400"><div className="text-center"><span className="mx-auto block h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-sky-400" /><p className="mt-4">Choosing today&apos;s best learning tasks...</p></div></div>;
  if (!plan) return <><EmptyPlanState {...setup} onGenerate={setup.hasGoal && setup.hasAssessment && setup.hasRoadmap ? () => void loadPlan() : undefined} />{toast && <p className="mx-auto mt-4 max-w-2xl rounded-xl border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-200">{toast}</p>}</>;

  const sorted = [...plan.items].sort((left, right) => Number(["completed", "skipped"].includes(left.status)) - Number(["completed", "skipped"].includes(right.status)) || left.order_index - right.order_index);
  return <div className="mx-auto max-w-5xl"><DailyPlanHeader plan={plan} streak={streak} /><div className="mt-7 flex items-center justify-between"><div><h2 className="text-2xl font-bold">Your focus queue</h2><p className="mt-1 text-sm text-slate-500">One task at a time. Progress over pressure.</p></div>{plan.completed_items_count === 0 && <button type="button" disabled={regenerating} onClick={() => void regenerate()} className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-300 disabled:opacity-50">{regenerating ? "Refreshing..." : "Regenerate Plan"}</button>}</div><div className="mt-5 space-y-4">{sorted.map((item) => <PlanItemCard key={item.id} item={item} onStatus={(status, minutes) => changeStatus(item, status, minutes)} />)}</div>{summary && !showCelebration && <div className="mt-7"><PlanSummaryCard summary={summary} /></div>}{showCelebration && summary && <CompletionCelebration name={user?.full_name.split(" ")[0] ?? "Learner"} summary={summary} onClose={() => setShowCelebration(false)} />}{toast && <div role="status" className="fixed bottom-5 right-5 z-[80] max-w-sm rounded-xl border border-slate-700 bg-slate-900 px-5 py-3 text-sm shadow-2xl">{toast}</div>}</div>;
}
