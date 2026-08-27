"use client";

import { useEffect, useRef, useState } from "react";

function clock(seconds: number): string {
  return `${Math.floor(seconds / 60).toString().padStart(2, "0")}:${(seconds % 60).toString().padStart(2, "0")}`;
}

export function SessionTimer({ estimatedMinutes, onComplete, onSkip }: { estimatedMinutes: number; onComplete: (minutes: number) => void; onSkip: () => void }): JSX.Element {
  const [startTime, setStartTime] = useState(() => Date.now());
  const [accumulated, setAccumulated] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [paused, setPaused] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [editedMinutes, setEditedMinutes] = useState<string>("");
  const accumulatedRef = useRef(accumulated);
  useEffect(() => { accumulatedRef.current = accumulated; }, [accumulated]);
  useEffect(() => {
    const update = (): void => setElapsed(accumulatedRef.current + (paused ? 0 : Math.floor((Date.now() - startTime) / 1000)));
    update(); const interval = window.setInterval(update, 1000); return () => window.clearInterval(interval);
  }, [paused, startTime]);
  const togglePause = (): void => {
    if (paused) { setStartTime(Date.now()); setPaused(false); }
    else { const total = accumulated + Math.floor((Date.now() - startTime) / 1000); setAccumulated(total); setElapsed(total); setPaused(true); }
  };
  const minutes = Math.max(1, Math.round(elapsed / 60));
  const percentage = Math.min(100, elapsed / Math.max(1, estimatedMinutes * 60) * 100);
  const over = elapsed > estimatedMinutes * 60;
  return <div className="mt-5 rounded-xl border border-sky-400/20 bg-slate-950/60 p-5"><div className="flex items-center justify-between"><p className="text-sm font-bold text-sky-300">⏱ Session Timer</p><span className={`text-xs font-semibold ${over ? "text-orange-300" : "text-slate-500"}`}>{over ? "Over time" : `~${Math.max(0, estimatedMinutes - Math.floor(elapsed / 60))} min remaining`}</span></div><p className="mt-4 text-center font-mono text-4xl font-bold tracking-wider">{clock(elapsed)}</p><p className="mt-1 text-center text-xs text-slate-500">elapsed · estimated {estimatedMinutes} min</p><div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-800"><div className={`h-full rounded-full transition-all ${over ? "bg-orange-400" : "bg-sky-400"}`} style={{ width: `${percentage}%` }} /></div><div className="mt-5 flex flex-wrap justify-center gap-3"><button type="button" onClick={() => setConfirming(true)} className="rounded-lg bg-emerald-400 px-4 py-2 text-sm font-bold text-slate-950">Mark Complete</button><button type="button" onClick={togglePause} className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-semibold">{paused ? "Resume" : "Take a Break"}</button><button type="button" onClick={onSkip} className="px-3 py-2 text-sm text-slate-500">Skip</button></div>{confirming && <div role="dialog" aria-modal="true" className="mt-5 rounded-xl border border-slate-700 bg-slate-900 p-4"><p className="font-semibold">You spent about {minutes} minute{minutes === 1 ? "" : "s"}. Does that sound right?</p><div className="mt-3 flex flex-wrap gap-2"><button type="button" onClick={() => onComplete(minutes)} className="rounded-lg bg-sky-400 px-4 py-2 text-sm font-bold text-slate-950">Yes, mark complete</button><input aria-label="Edit minutes" type="number" min="0" max="1440" value={editedMinutes} onChange={(event) => setEditedMinutes(event.target.value)} placeholder="Edit time" className="w-24 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm" /><button type="button" disabled={editedMinutes === ""} onClick={() => onComplete(Math.max(0, Number(editedMinutes)))} className="rounded-lg border border-slate-700 px-3 py-2 text-sm disabled:opacity-40">Use edited time</button></div></div>}</div>;
}
