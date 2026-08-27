"use client";

import { useEffect, useState } from "react";
import { ExerciseHub } from "@/components/exercises/ExerciseHub";
import { ApiError, apiGet } from "@/lib/api";
import type { ExerciseHistory, Recommendation } from "@/lib/exercises";
import type { LearnerContext } from "@/lib/tutor";

export default function ExercisesPage(): JSX.Element {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [history, setHistory] = useState<ExerciseHistory[]>([]);
  const [context, setContext] = useState<LearnerContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([
      apiGet<Recommendation[]>("/api/v1/exercises/recommended"),
      apiGet<ExerciseHistory[]>("/api/v1/exercises/history?limit=8"),
      apiGet<LearnerContext>("/api/v1/tutor/context"),
    ]).then(([items, recent, learner]) => {
      if (active) { setRecommendations(items); setHistory(recent); setContext(learner); }
    }).catch((reason: unknown) => {
      if (active) setError(reason instanceof ApiError ? reason.message : "Practice recommendations could not be loaded.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  if (loading) return <div className="flex min-h-[65vh] items-center justify-center"><div className="text-center"><span className="mx-auto block h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-purple-400" /><p className="mt-4 text-slate-400">Finding the best practice for you...</p></div></div>;
  if (!context) return <p className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 text-red-200">{error ?? "Learner context is unavailable."}</p>;
  return <><ExerciseHub recommendations={recommendations} history={history} context={context} />{error && <p className="fixed bottom-5 right-5 rounded-xl bg-slate-900 p-4 text-sm">{error}</p>}</>;
}
