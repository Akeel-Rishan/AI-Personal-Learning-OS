"use client";

import Link from "next/link";
import { ProgressBar } from "@/components/assessment/ProgressBar";

function timer(seconds: number): string {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  return `${minutes}:${(seconds % 60).toString().padStart(2, "0")}`;
}

interface Props {
  goalTitle: string;
  completed: number;
  total: number;
  elapsedSeconds: number;
  canSubmit: boolean;
  isSubmitting: boolean;
  feedbackVisible: boolean;
  onSkip: () => void;
  onSubmit: () => void;
  children: React.ReactNode;
}

export function AssessmentShell(props: Props): JSX.Element {
  const number = Math.min(props.total, props.completed + 1);
  return (
    <div className="min-h-screen bg-slate-950 pb-28 pt-28 text-slate-100">
      <header className="fixed inset-x-0 top-0 z-30 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6">
          <Link href="/dashboard" className="shrink-0 font-bold tracking-tight"><span className="text-sky-400">AI</span><span className="hidden sm:inline"> Learning OS</span></Link>
          <p className="max-w-md truncate text-center text-sm font-semibold text-slate-300">Initial Assessment — {props.goalTitle}</p>
          <div className="shrink-0 text-right text-xs text-slate-400"><p>Question {number} of {props.total}</p><p className="mt-1 font-mono text-slate-500">{timer(props.elapsedSeconds)}</p></div>
        </div>
        <div className="mx-auto max-w-7xl px-4 pb-3 sm:px-6"><ProgressBar completed={props.completed} total={props.total} /></div>
      </header>
      <main className="mx-auto max-w-[720px] px-4 sm:px-6">{props.children}</main>
      {!props.feedbackVisible && <footer className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-800 bg-slate-950/95 backdrop-blur"><div className="mx-auto flex h-20 max-w-[720px] items-center justify-between px-4 sm:px-6"><button type="button" disabled={props.isSubmitting} onClick={props.onSkip} className="text-sm font-semibold text-slate-500 transition hover:text-slate-200 disabled:opacity-50">Skip this question</button><button type="button" disabled={!props.canSubmit || props.isSubmitting} onClick={props.onSubmit} className="rounded-xl bg-sky-400 px-6 py-3 font-bold text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500">{props.isSubmitting ? "Checking..." : "Submit Answer"}</button></div></footer>}
    </div>
  );
}
