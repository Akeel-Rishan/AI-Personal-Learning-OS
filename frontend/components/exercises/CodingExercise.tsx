"use client";

import { CodeEditor } from "@/components/exercises/CodeEditor";
import type { CodeReview, Exercise } from "@/lib/exercises";

interface CodingExerciseProps { exercise: Exercise; value: string; onChange: (value: string) => void; disabled: boolean; reviewing: boolean; review: CodeReview | null; onRunTests: () => void }

export function CodingExercise({ exercise, value, onChange, disabled, reviewing, review, onRunTests }: CodingExerciseProps): JSX.Element {
  const testSummary = review && review.total_test_cases !== null && review.total_test_cases !== undefined ? ` · ${review.passed_test_cases ?? 0}/${review.total_test_cases} tests` : " · AI review ready";
  return (
    <div>
      <div className="rounded-xl border border-sky-400/20 bg-sky-400/5 p-5"><p className="text-xs font-bold uppercase tracking-wider text-sky-300">Problem Statement</p><p className="mt-3 leading-7 text-slate-200">{exercise.content.problem_statement}</p></div>
      {exercise.content.constraints && exercise.content.constraints.length > 0 && <div className="mt-5"><p className="text-sm font-semibold">Constraints</p><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-400">{exercise.content.constraints.map((item) => <li key={item}>{item}</li>)}</ul></div>}
      {exercise.content.example_input && <div className="mt-5 grid gap-3 sm:grid-cols-2"><div className="rounded-lg bg-slate-950 p-3 font-mono text-xs"><span className="text-slate-600">Input</span><p className="mt-1 text-slate-300">{exercise.content.example_input}</p></div><div className="rounded-lg bg-slate-950 p-3 font-mono text-xs"><span className="text-slate-600">Output</span><p className="mt-1 text-emerald-300">{exercise.content.example_output}</p></div></div>}
      {exercise.content.test_cases && <details className="mt-5 rounded-xl border border-slate-800 p-4"><summary className="cursor-pointer text-sm font-semibold">Test cases ({exercise.content.test_cases.length})</summary><div className="mt-3 space-y-2">{exercise.content.test_cases.map((test, index) => <div key={index} className="rounded-lg bg-slate-950 p-3 text-xs text-slate-400">{test.description}: <code>{test.input}</code> → <code className="text-emerald-300">{test.expected_output}</code></div>)}</div></details>}
      <p className="mb-2 mt-6 text-sm font-semibold">Your Solution</p>
      <CodeEditor value={value} onChange={onChange} starterCode={exercise.content.starter_code} disabled={disabled} />
      <div className="mt-4 flex items-center gap-3"><button type="button" disabled={disabled || reviewing || value.trim().length < 10} onClick={onRunTests} className="rounded-lg border border-purple-400/30 px-4 py-2 text-sm font-bold text-purple-300 disabled:opacity-40">{reviewing ? "Running tests..." : "Run Tests (simulated)"}</button>{review && <span className="text-sm text-slate-400">Estimated {Math.round(review.overall_score * 100)}%{testSummary}</span>}</div>
    </div>
  );
}
