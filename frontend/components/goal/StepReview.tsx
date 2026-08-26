"use client";

import { useEffect, useMemo, useState } from "react";
import type { GoalDecomposition } from "@/lib/goals";

interface StepReviewProps {
  status: "idle" | "loading" | "success" | "error";
  result: GoalDecomposition | null;
  error: string | null;
  onRetry: () => void;
  onConfirm: () => void;
}

const loadingMessages = [
  "Understanding your goal...",
  "Mapping required skills...",
  "Checking your existing knowledge...",
  "Building your personalized path...",
  "Almost ready...",
];

const categoryStyles: Record<string, string> = {
  programming: "border-blue-400/30 bg-blue-400/10 text-blue-300",
  mathematics: "border-purple-400/30 bg-purple-400/10 text-purple-300",
  "data-science": "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  ml: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  devops: "border-slate-500 bg-slate-700/40 text-slate-300",
};

function categoryLabel(value: string): string {
  return value.split("-").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

export function StepReview({ status, result, error, onRetry, onConfirm }: StepReviewProps): JSX.Element {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    if (status !== "loading") return;
    setMessageIndex(0);
    const interval = window.setInterval(() => {
      setMessageIndex((index) => Math.min(index + 1, loadingMessages.length - 1));
    }, 2000);
    return () => window.clearInterval(interval);
  }, [status]);

  const groupedSkills = useMemo(() => {
    if (!result) return [];
    const groups = new Map<string, typeof result.required_skills>();
    [...result.required_skills]
      .sort((left, right) => left.priority_order - right.priority_order)
      .forEach((item) => {
        const category = item.skill.category;
        groups.set(category, [...(groups.get(category) ?? []), item]);
      });
    return Array.from(groups.entries());
  }, [result]);

  if (status === "idle" || status === "loading") {
    return (
      <section className="flex min-h-[430px] animate-[wizard-enter_.3s_ease-out] flex-col items-center justify-center text-center" aria-live="polite">
        <div className="relative h-20 w-20">
          <span className="absolute inset-0 animate-ping rounded-full bg-sky-400/15" />
          <span className="absolute inset-2 animate-spin rounded-full border-4 border-slate-700 border-t-sky-400" />
          <span className="absolute inset-[30px] rounded-full bg-sky-300" />
        </div>
        <h1 className="mt-8 text-3xl font-bold">Analyzing your goal...</h1>
        <p className="mt-3 text-sky-300 transition-all">{loadingMessages[messageIndex]}</p>
        <div className="mt-8 flex gap-2">
          {loadingMessages.map((message, index) => <span key={message} className={`h-1.5 rounded-full transition-all ${index <= messageIndex ? "w-8 bg-sky-400" : "w-4 bg-slate-700"}`} />)}
        </div>
        <p className="mt-6 max-w-md text-sm leading-6 text-slate-500">OpenAI is matching your goal to the skill graph. This can take several seconds.</p>
      </section>
    );
  }

  if (status === "error" || !result) {
    return (
      <section className="flex min-h-[430px] animate-[wizard-enter_.3s_ease-out] flex-col items-center justify-center text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10 text-3xl text-red-300">!</div>
        <h1 className="mt-6 text-2xl font-bold">We couldn&apos;t build your plan</h1>
        <p className="mt-3 max-w-lg leading-7 text-slate-400">{error ?? "The roadmap service is temporarily unavailable. Please try again."}</p>
        <button type="button" onClick={onRetry} className="mt-7 rounded-xl bg-sky-400 px-6 py-3 font-semibold text-slate-950 transition hover:bg-sky-300">Try again</button>
      </section>
    );
  }

  return (
    <section className="animate-[wizard-enter_.3s_ease-out]">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400">Your plan is ready</p>
      <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Review your personalized path</h1>

      <div className="mt-7 rounded-2xl border border-sky-400/25 bg-gradient-to-br from-sky-400/15 via-slate-900 to-indigo-500/10 p-6 sm:p-7">
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-sky-300 px-3 py-1 text-xs font-bold text-slate-950">~{result.estimated_weeks} weeks</span>
          <span className="rounded-full border border-indigo-300/30 bg-indigo-400/10 px-3 py-1 text-xs font-semibold capitalize text-indigo-200">{result.difficulty_assessment}</span>
          <span className="rounded-full border border-slate-600 bg-slate-800 px-3 py-1 text-xs text-slate-300">{result.required_skills.length} skills</span>
        </div>
        <p className="mt-5 text-lg leading-8 text-slate-200">{result.summary}</p>
      </div>

      <div className="mt-8 space-y-7">
        {groupedSkills.map(([category, skills]) => (
          <div key={category}>
            <h2 className="text-sm font-bold uppercase tracking-[0.15em] text-slate-400">{categoryLabel(category)}</h2>
            <div className="mt-3 grid gap-3 lg:grid-cols-2">
              {skills.map((item) => (
                <article key={item.skill.id} className="flex gap-4 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-800 text-sm font-bold text-sky-300">{item.priority_order}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{item.skill.name}</h3>
                      <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${categoryStyles[category] ?? categoryStyles.devops}`}>{categoryLabel(category)}</span>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] ${item.is_required ? "bg-rose-400/10 text-rose-300" : "bg-slate-700 text-slate-300"}`}>{item.is_required ? "Required" : "Recommended"}</span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">{item.skill.estimated_hours ?? 0} estimated hours</p>
                    {item.reason && <p className="mt-2 text-sm leading-6 text-slate-400">{item.reason}</p>}
                  </div>
                </article>
              ))}
            </div>
          </div>
        ))}
      </div>

      {result.warnings.length > 0 && (
        <div className="mt-8 space-y-2">
          {result.warnings.map((warning) => <p key={warning} className="rounded-xl border border-amber-400/25 bg-amber-400/5 px-4 py-3 text-sm text-amber-200"><span className="mr-2">⚠</span>{warning}</p>)}
        </div>
      )}

      <button type="button" onClick={onConfirm} className="mt-9 w-full rounded-xl bg-sky-400 px-6 py-4 text-base font-bold text-slate-950 shadow-lg shadow-sky-500/10 transition hover:-translate-y-0.5 hover:bg-sky-300 sm:w-auto">This looks great, create my roadmap →</button>
    </section>
  );
}
