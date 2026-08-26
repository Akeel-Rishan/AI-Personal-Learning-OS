"use client";

import type { SkillScore } from "@/lib/assessments";

function color(score: number): string {
  if (score < 40) return "bg-red-500";
  if (score < 70) return "bg-amber-500";
  if (score < 90) return "bg-blue-500";
  return "bg-emerald-500";
}

export function ResultsChart({ skills }: { skills: SkillScore[] }): JSX.Element {
  const grouped = skills.reduce<Record<string, SkillScore[]>>((result, skill) => { (result[skill.category] ??= []).push(skill); return result; }, {});
  return <div className="space-y-7">{Object.entries(grouped).map(([category, items]) => <section key={category}><h3 className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-slate-500">{category.replaceAll("-", " ")}</h3><div className="space-y-4">{items.map((skill) => <div key={skill.skill_id} className="grid grid-cols-[minmax(90px,180px)_1fr_48px] items-center gap-3"><span className="truncate text-sm font-medium" title={skill.skill_name}>{skill.skill_name}</span><div className="h-3 overflow-hidden rounded-full bg-slate-800"><div className={`h-full origin-left animate-result-bar rounded-full ${color(skill.mastery_percentage)}`} style={{ width: `${skill.mastery_percentage}%` }} /></div><span className="text-right text-sm font-bold">{Math.round(skill.mastery_percentage)}%</span></div>)}</div></section>)}</div>;
}
