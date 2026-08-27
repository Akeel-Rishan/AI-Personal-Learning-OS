"use client";

import { CodeEditor } from "@/components/exercises/CodeEditor";
import type { Exercise } from "@/lib/exercises";

export interface DebuggingAnswer { description: string; code: string }

export function DebuggingExercise({ exercise, value, onChange, disabled }: { exercise: Exercise; value: DebuggingAnswer; onChange: (value: DebuggingAnswer) => void; disabled: boolean }): JSX.Element {
  const buggy = exercise.content.buggy_code ?? exercise.content.starter_code ?? "";
  return <div><p className="text-lg font-semibold leading-8">{exercise.content.problem_statement}</p><div className="mt-5"><p className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">Buggy code</p><pre className="overflow-x-auto rounded-xl border border-red-400/20 bg-[#1e1e1e] p-4 font-mono text-sm leading-7 text-slate-300"><code>{buggy.split("\n").map((line, index) => <span key={index} className="table-row"><span className="table-cell select-none pr-5 text-right text-slate-600">{index + 1}</span><span className="table-cell whitespace-pre">{line}</span></span>)}</code></pre></div><label htmlFor="bug-description" className="mt-5 block text-sm font-semibold">What is wrong?</label><textarea id="bug-description" value={value.description} disabled={disabled} onChange={(event) => onChange({ ...value, description: event.target.value })} rows={3} className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 p-4 outline-none focus:border-sky-400" placeholder="Describe the bug and why it fails..." /><p className="mb-2 mt-5 text-sm font-semibold">Your fixed code</p><CodeEditor value={value.code} onChange={(code) => onChange({ ...value, code })} starterCode={buggy} disabled={disabled} minHeight={260} /></div>;
}
