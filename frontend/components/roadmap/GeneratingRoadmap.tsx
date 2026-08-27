"use client";

import { useEffect, useState } from "react";

const steps = ["Analyzing your goal", "Reviewing your assessment results", "Mapping skill dependencies", "Calculating optimal learning order", "Organizing skills into phases", "Generating your schedule"];

export function GeneratingRoadmap(): JSX.Element {
  const [current, setCurrent] = useState(0);
  useEffect(() => { const interval = window.setInterval(() => setCurrent((value) => Math.min(steps.length - 1, value + 1)), 2000); return () => window.clearInterval(interval); }, []);
  return <section className="mx-auto flex min-h-[70vh] max-w-xl flex-col items-center justify-center text-center"><div className="relative flex h-24 w-24 items-center justify-center rounded-3xl border border-sky-400/30 bg-sky-400/10"><span className="absolute inset-0 animate-ping rounded-3xl border border-sky-400/20" /><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-12 w-12 text-sky-300"><path d="M9.5 4A3.5 3.5 0 0 0 6 7.5v1A3 3 0 0 0 4 14a3 3 0 0 0 3 3h2.5M14.5 4A3.5 3.5 0 0 1 18 7.5v1a3 3 0 0 1 2 5.5 3 3 0 0 1-3 3h-2.5M12 3v18M8 9h4M12 15h4" /></svg></div><h1 className="mt-7 text-3xl font-bold">Building Your Personalized Roadmap</h1><p className="mt-3 text-slate-400">Balancing prerequisites, your current mastery, and daily study time.</p><div className="mt-8 w-full space-y-3 text-left">{steps.map((step, index) => <div key={step} className={`flex items-center gap-3 rounded-xl border px-4 py-3 transition duration-500 ${index <= current ? "border-sky-400/20 bg-sky-400/5 opacity-100" : "border-slate-800 opacity-35"}`}><span className={index < current ? "text-emerald-400" : index === current ? "animate-spin text-sky-400" : "text-slate-600"}>{index < current ? "✓" : index === current ? "◌" : "·"}</span><span>{step}</span></div>)}</div><div className="mt-7 h-1.5 w-full overflow-hidden rounded-full bg-slate-800"><div className="h-full bg-gradient-to-r from-sky-400 to-indigo-400 transition-all duration-700" style={{ width: `${((current + 1) / steps.length) * 100}%` }} /></div><p className="mt-3 text-xs text-slate-500">This usually takes about 15 seconds...</p></section>;
}
