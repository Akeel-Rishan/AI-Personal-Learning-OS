"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ExerciseSession } from "@/components/exercises/ExerciseSession";
import { ApiError, apiGet, apiPost } from "@/lib/api";
import type { Exercise } from "@/lib/exercises";
import type { LearnerContext } from "@/lib/tutor";

interface Skill { id: string; name: string; slug: string }

export default function PracticePage(): JSX.Element {
  const params = useParams<{ skillSlug: string }>(); const search = useSearchParams(); const planItemId = search.get("planItemId") ?? undefined;
  const [skill, setSkill] = useState<Skill | null>(null); const [exercises, setExercises] = useState<Exercise[]>([]); const [mastery, setMastery] = useState(0); const [loading, setLoading] = useState(true); const [generating, setGenerating] = useState(false); const [error, setError] = useState<string | null>(null); const [batch, setBatch] = useState(0);
  const load = useCallback(async (): Promise<void> => { setLoading(true); setError(null); try { const found = await apiGet<Skill[]>(`/api/v1/skills?search=${encodeURIComponent(params.skillSlug)}`); const exact = found.find((item) => item.slug === params.skillSlug) ?? found[0]; if (!exact) throw new ApiError("Skill not found", 404); setSkill(exact); const [items, context] = await Promise.all([apiGet<Exercise[]>(`/api/v1/exercises/skill/${exact.id}?limit=5&exclude_completed=false`), apiGet<LearnerContext>("/api/v1/tutor/context")]); setExercises(items.slice(0, 5)); setMastery(context.skill_mastery.find((item) => item.id === exact.id)?.mastery ?? 0); } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Exercises could not be loaded."); } finally { setLoading(false); } }, [params.skillSlug]);
  useEffect(() => { void load(); }, [load]);
  const more = async (): Promise<void> => { if (!skill) return; setGenerating(true); try { await apiPost(`/api/v1/exercises/generate`, { skill_id: skill.id, count: 5 }); sessionStorage.removeItem(`exercise_session_${skill.id}`); await load(); setBatch((value) => value + 1); } catch (reason) { setError(reason instanceof ApiError ? reason.message : "More exercises could not be generated."); } finally { setGenerating(false); } };
  if (loading || generating) return <div className="flex min-h-[65vh] items-center justify-center"><div className="text-center"><span className="mx-auto block h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-purple-400" /><p className="mt-4 text-slate-400">{generating ? "Generating targeted exercises..." : "Preparing your practice session..."}</p></div></div>;
  if (error || !skill || exercises.length === 0) return <div className="mx-auto max-w-xl rounded-2xl border border-red-500/20 bg-red-500/5 p-7 text-center"><h1 className="text-xl font-bold">Practice unavailable</h1><p className="mt-3 text-red-200">{error ?? "No exercises are available."}</p><button type="button" onClick={() => void load()} className="mt-5 rounded-lg bg-sky-400 px-4 py-2 font-bold text-slate-950">Try again</button></div>;
  return <ExerciseSession key={`${skill.id}-${batch}`} exercises={exercises} skillId={skill.id} skillName={skill.name} skillSlug={skill.slug} initialMastery={mastery} planItemId={planItemId} onPracticeMore={() => void more()} />;
}
