"use client";

import Link from "next/link";
import type { AttemptFeedback, Exercise } from "@/lib/exercises";

interface ExerciseResultsProps { skillName: string; skillSlug: string; exercises: Exercise[]; results: Array<AttemptFeedback | null>; durationMinutes: number; initialMastery: number; onPracticeMore: () => void; onAskTutor: () => void }

export function ExerciseResults({ skillName, skillSlug, exercises, results, durationMinutes, initialMastery, onPracticeMore, onAskTutor }: ExerciseResultsProps): JSX.Element {
  const completed = results.filter(Boolean) as AttemptFeedback[];
  const correct = completed.filter((item) => item.is_correct).length;
  const ending = completed.at(-1)?.new_mastery ?? initialMastery;
  const accuracy = exercises.length ? Math.round(correct / exercises.length * 100) : 0;
  return (
    <div className="mx-auto max-w-4xl">
      <div className="text-center"><p className="text-xs font-bold uppercase tracking-[.2em] text-emerald-300">Session Complete</p><h1 className="mt-3 text-4xl font-black">{skillName} Practice 🎯</h1><p className="mt-3 text-slate-400">{exercises.length} exercises · {durationMinutes} minutes</p></div>
      <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">{[[`${correct}/${exercises.length}`, "Correct"], [`${accuracy}%`, "Accuracy"], [`${ending >= initialMastery ? "+" : ""}${Math.round((ending - initialMastery) * 100)}%`, "Mastery"], [`+${correct * 30} XP`, "Earned"]].map(([value, label]) => <div key={label} className="rounded-xl border border-slate-800 bg-slate-900 p-5 text-center"><b className="text-2xl">{value}</b><p className="mt-1 text-xs text-slate-500">{label}</p></div>)}</div>
      <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6"><div className="flex justify-between text-sm"><span>{skillName} Mastery</span><b>{Math.round(initialMastery * 100)}% → {Math.round(ending * 100)}%</b></div><div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-800"><div className="h-full rounded-full bg-gradient-to-r from-sky-400 to-emerald-400" style={{ width: `${ending * 100}%` }} /></div><div className="mt-6 space-y-2">{exercises.map((exercise, index) => <div key={exercise.id} className="flex items-center justify-between gap-3 rounded-lg bg-slate-950/50 px-4 py-3 text-sm"><span className="truncate">{results[index]?.is_correct ? "✅" : "❌"} {exercise.title}</span><span className="text-slate-500">{results[index] ? `${Math.round(results[index]!.score * 100)}% · try ${results[index]!.attempt_number}` : "Skipped"}</span></div>)}</div></section>
      <div className="mt-7 flex flex-wrap justify-center gap-3"><button type="button" onClick={onPracticeMore} className="rounded-xl bg-sky-400 px-5 py-3 font-bold text-slate-950">Practice More</button><Link href="/plan" className="rounded-xl border border-slate-700 px-5 py-3 font-bold">Go to Plan</Link>{correct < exercises.length && <button type="button" onClick={onAskTutor} className="rounded-xl border border-indigo-400/30 px-5 py-3 font-bold text-indigo-200">Ask Tutor About Mistakes</button>}<Link href={`/exercises/practice/${skillSlug}`} className="sr-only">Practice {skillName}</Link></div>
    </div>
  );
}
