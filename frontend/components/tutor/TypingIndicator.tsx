"use client";

import { useEffect, useState } from "react";

export function TypingIndicator(): JSX.Element {
  const [slow, setSlow] = useState(false);
  useEffect(() => { const timer = window.setTimeout(() => setSlow(true), 5000); return () => window.clearTimeout(timer); }, []);
  return <div className="flex items-start gap-3"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-400/15 text-lg">AI</span><div><div className="flex w-fit gap-1.5 rounded-2xl rounded-tl-sm border border-slate-800 bg-slate-900 px-5 py-4">{[0, 1, 2].map((index) => <span key={index} className="h-2 w-2 animate-tutor-bounce rounded-full bg-sky-400" style={{ animationDelay: `${index * 150}ms` }} />)}</div><p className="mt-2 text-xs text-slate-500">AI Tutor is thinking...{slow ? " Complex questions may take a moment." : ""}</p></div></div>;
}
