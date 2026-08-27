"use client";

import { SessionTimer } from "@/components/plan/SessionTimer";
import type { DailyPlanItem, PlanItemStatus } from "@/lib/plans";
import { useRouter } from "next/navigation";

const typeStyle: Record<string, { icon: string; color: string }> = {
  lesson: { icon: "▤", color: "text-blue-400" },
  exercise: { icon: "</>", color: "text-purple-400" },
  review: { icon: "↻", color: "text-emerald-400" },
  assessment: { icon: "✓", color: "text-red-400" },
  practice: { icon: "✎", color: "text-orange-400" },
  project: { icon: "▱", color: "text-amber-400" },
};

interface PlanItemCardProps {
  item: DailyPlanItem;
  onStatus: (status: PlanItemStatus, minutes?: number) => void;
  onExerciseStart?: () => void;
}

export function PlanItemCard({ item, onStatus, onExerciseStart }: PlanItemCardProps): JSX.Element {
  const router = useRouter();
  const type = typeStyle[item.item_type] ?? typeStyle.lesson;
  const completed = item.status === "completed";
  const skipped = item.status === "skipped";
  return (
    <article className={`rounded-2xl border border-slate-800 border-l-4 bg-slate-900/60 p-5 transition sm:p-6 ${completed ? "border-l-emerald-400 opacity-75" : skipped ? "border-l-slate-600 opacity-60" : item.status === "in_progress" ? "border-l-sky-400 shadow-lg shadow-sky-950/20" : "border-l-slate-700"}`}>
      <div className="flex items-start gap-4">
        <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-950 font-bold ${completed ? "text-emerald-400" : type.color}`}>{completed ? "✓" : skipped ? "−" : type.icon}</span>
        <div className="min-w-0 flex-1"><h2 className={`font-bold leading-6 sm:text-lg ${completed || skipped ? "text-slate-500 line-through" : ""}`}>{item.title}</h2><p className="mt-2 text-xs capitalize text-slate-500">{item.item_type} · {item.skill_name ?? "General"} · {item.estimated_minutes} min</p>{item.description && item.status === "in_progress" && <p className="mt-4 leading-7 text-slate-400">{item.description}</p>}</div>
        {item.status === "pending" && <button type="button" onClick={() => { onStatus("in_progress"); if (onExerciseStart) onExerciseStart(); else if (["exercise", "practice"].includes(item.item_type) && item.skill_slug) router.push(`/exercises/practice/${item.skill_slug}?planItemId=${item.id}`); }} className="shrink-0 rounded-lg bg-sky-400 px-4 py-2 text-sm font-bold text-slate-950">Start</button>}
        {skipped && <button type="button" onClick={() => onStatus("pending")} className="shrink-0 text-sm font-semibold text-sky-300">Undo</button>}
      </div>
      {item.status === "in_progress" && <SessionTimer estimatedMinutes={item.estimated_minutes} onComplete={(minutes) => onStatus("completed", minutes)} onSkip={() => onStatus("skipped")} />}
      {completed && item.completed_at && <p className="mt-4 text-xs text-emerald-400">Completed {new Intl.RelativeTimeFormat(undefined, { numeric: "auto" }).format(Math.min(0, Math.round((new Date(item.completed_at).getTime() - Date.now()) / 60000)), "minute")}</p>}
    </article>
  );
}
