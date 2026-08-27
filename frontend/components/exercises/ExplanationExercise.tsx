"use client";

import type { Exercise } from "@/lib/exercises";

export function ExplanationExercise({ exercise, value, onChange, disabled }: { exercise: Exercise; value: string; onChange: (value: string) => void; disabled: boolean }): JSX.Element {
  const words = value.trim() ? value.trim().split(/\s+/).length : 0;
  return <div><p className="text-lg font-semibold leading-8">{exercise.content.problem_statement}</p><div className="mt-6 rounded-xl border border-slate-700 bg-slate-950/60 p-4"><label htmlFor="explanation-answer" className="text-sm font-semibold text-slate-300">Your explanation</label><textarea id="explanation-answer" value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} rows={8} maxLength={8000} placeholder="Explain it as if teaching someone who has never seen this concept..." className="mt-3 w-full resize-y bg-transparent leading-7 outline-none placeholder:text-slate-600" /><p className="mt-3 text-xs text-slate-500">💡 Use intuition, the key rule, and one example.</p></div><div className="mt-3 flex justify-between text-xs"><span className={words >= 30 ? "text-emerald-400" : "text-slate-500"}>Word count: {words}</span><span className="text-slate-600">Minimum 30 words</span></div></div>;
}
