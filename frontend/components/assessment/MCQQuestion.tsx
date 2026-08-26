"use client";

import { useEffect } from "react";

interface Props {
  options: string[];
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  feedback?: { is_correct: boolean; correct_answer: string } | null;
}

export function MCQQuestion({ options, value, onChange, onSubmit, disabled, feedback }: Props): JSX.Element {
  useEffect(() => {
    const handleKey = (event: KeyboardEvent): void => {
      if (disabled) return;
      const number = Number(event.key);
      if (number >= 1 && number <= options.length) onChange(options[number - 1]);
      if (event.key === "Enter" && value) onSubmit();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [disabled, onChange, onSubmit, options, value]);

  return (
    <div className="grid gap-3">
      {options.map((option, index) => {
        const selected = value === option;
        const correct = feedback && option === feedback.correct_answer;
        const wrong = feedback && selected && !feedback.is_correct;
        const colors = correct ? "border-emerald-400 bg-emerald-400/10" : wrong ? "border-red-400 bg-red-400/10" : selected ? "border-sky-400 bg-sky-400/10" : "border-slate-700 bg-slate-900/60 hover:border-slate-500";
        return <button key={option} type="button" disabled={disabled} onClick={() => onChange(option)} className={`flex min-h-16 items-center gap-4 rounded-xl border p-4 text-left transition ${colors}`}><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-800 text-sm font-bold text-slate-300">{index + 1}</span><span className="leading-6">{option}</span></button>;
      })}
      <p className="text-xs text-slate-500">Keyboard: press 1–4 to choose, then Enter to submit.</p>
    </div>
  );
}
