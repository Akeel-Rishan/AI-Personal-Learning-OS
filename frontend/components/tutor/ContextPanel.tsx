"use client";

import type { ExplanationStyle, LearnerContext } from "@/lib/tutor";

const styles: Array<{ value: ExplanationStyle; label: string }> = [
  { value: "visual", label: "Visual + Examples" }, { value: "mathematical", label: "Mathematical / Formal" },
  { value: "step_by_step", label: "Step by Step" }, { value: "analogies", label: "Analogies & Stories" },
  { value: "balanced", label: "Balanced" },
];

function masteryColor(score: number): string {
  if (score < 0.4) return "bg-red-400";
  if (score < 0.6) return "bg-amber-400";
  if (score < 0.8) return "bg-sky-400";
  return "bg-emerald-400";
}

export function ContextPanel({ context, savingStyle, onStyleChange, onClose }: { context: LearnerContext; savingStyle: boolean; onStyleChange: (style: ExplanationStyle) => void; onClose?: () => void }): JSX.Element {
  return <aside className="h-full overflow-y-auto bg-slate-950"><div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-800 bg-slate-950 p-4"><h2 className="font-bold">Tutor Context</h2>{onClose && <button type="button" onClick={onClose} aria-label="Close context" className="rounded-lg p-2 text-slate-400 hover:bg-slate-800">×</button>}</div><div className="divide-y divide-slate-800 text-sm"><section className="p-5"><h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">About You</h3><p className="mt-3 text-slate-300">Goal: {context.goal_title}</p><p className="mt-2 text-slate-400">🔥 {context.streak_days} day streak</p><p className="mt-1 text-slate-400">{context.total_xp.toLocaleString()} XP</p></section><section className="p-5"><h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Current Focus</h3><p className="mt-3 font-semibold text-slate-300">{context.current_phase}</p><p className="mt-2 leading-6 text-slate-500">Today: {context.today_plan_items.join(", ") || "No plan scheduled"}</p></section><section className="p-5"><h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Your Skills</h3><div className="mt-4 space-y-4">{context.skill_mastery.length === 0 && <p className="text-slate-500">Complete an assessment to establish mastery.</p>}{context.skill_mastery.map((skill) => <div key={skill.id}><div className="flex justify-between gap-2 text-xs"><span className="truncate text-slate-300">{skill.name}{skill.mastery < .5 ? " ⚠" : ""}</span><span className="text-slate-500">{Math.round(skill.mastery * 100)}%</span></div><div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-800"><div className={`h-full rounded-full ${masteryColor(skill.mastery)}`} style={{ width: `${skill.mastery * 100}%` }} /></div></div>)}</div></section>{context.weak_skills.length > 0 && <section className="p-5"><h3 className="text-xs font-bold uppercase tracking-wider text-amber-300">⚠ Weak Areas</h3><p className="mt-3 leading-6 text-slate-500">The tutor will give these areas extra attention.</p><ul className="mt-2 space-y-1 text-slate-300">{context.weak_skills.map((skill) => <li key={skill}>· {skill}</li>)}</ul></section>}<section className="p-5"><label htmlFor="explanation-style" className="text-xs font-bold uppercase tracking-wider text-slate-500">Explanation Style</label><select id="explanation-style" disabled={savingStyle} value={context.preferred_style} onChange={(event) => onStyleChange(event.target.value as ExplanationStyle)} className="mt-3 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 disabled:opacity-50">{styles.map((style) => <option key={style.value} value={style.value}>{style.label}</option>)}</select></section></div></aside>;
}
