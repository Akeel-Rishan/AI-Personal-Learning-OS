"use client";

import { useEffect } from "react";
import type { Exercise, AttemptFeedback } from "@/lib/exercises";

export function MCQExercise({ exercise, value, onChange, onSubmit, feedback }: { exercise: Exercise; value: string; onChange: (value: string) => void; onSubmit: () => void; feedback: AttemptFeedback | null }): JSX.Element {
  const options = exercise.content.options ?? [];
  useEffect(() => {
    const handler = (event: KeyboardEvent): void => { if (feedback) return; const index = Number(event.key) - 1; if (index >= 0 && index < options.length) onChange(options[index]); if (event.key === "Enter" && value) onSubmit(); };
    window.addEventListener("keydown", handler); return () => window.removeEventListener("keydown", handler);
  }, [feedback, onChange, onSubmit, options, value]);
  return <div><p className="text-lg font-semibold leading-8">{exercise.content.problem_statement}</p><div className="mt-6 grid gap-3">{options.map((option, index) => { const selected = value === option; const correct = feedback?.correct_answer === option; const wrong = Boolean(feedback && selected && !feedback.is_correct); return <button type="button" key={option} disabled={Boolean(feedback)} onClick={() => onChange(option)} className={`flex min-h-16 items-center gap-4 rounded-xl border p-4 text-left transition ${correct ? "border-emerald-400 bg-emerald-400/10" : wrong ? "border-red-400 bg-red-400/10" : selected ? "border-sky-400 bg-sky-400/10" : "border-slate-700 bg-slate-950/60 hover:border-slate-500"}`}><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-800 text-sm font-bold">{feedback ? correct ? "✓" : wrong ? "×" : index + 1 : index + 1}</span><span>{option}</span></button>; })}</div>{feedback && exercise.content.explanation && <p className="mt-5 rounded-xl bg-slate-950/60 p-4 text-sm leading-7 text-slate-400">{exercise.content.explanation}</p>}<p className="mt-3 text-xs text-slate-600">Keyboard: 1–4 to select, Enter to submit.</p></div>;
}
