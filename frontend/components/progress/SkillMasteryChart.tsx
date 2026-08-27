"use client";

import { useMemo, useState } from "react";
import type { MasteryPoint } from "@/lib/progress";
import { useChartSize } from "./useChartSize";

interface Series { name: string; color: string; values: MasteryPoint[] }
export function SkillMasteryChart({ points }: { points: MasteryPoint[] }): JSX.Element {
  const { ref, width } = useChartSize(); const [selected, setSelected] = useState("all");
  const height = 280; const pad = { l: 42, r: 16, t: 20, b: 34 };
  const names = useMemo(() => Array.from(new Set(points.map(point => point.skill_name).filter((name): name is string => Boolean(name)))).sort(), [points]);
  const series = useMemo<Series[]>(() => {
    if (selected !== "all") return [{ name: selected, color: "#38bdf8", values: points.filter(point => point.skill_name === selected).sort((a, b) => a.date.localeCompare(b.date)) }];
    const daily = new Map<string, MasteryPoint[]>();
    points.forEach(point => daily.set(point.date, [...(daily.get(point.date) ?? []), point]));
    const aggregate = Array.from(daily.entries()).sort(([left], [right]) => left.localeCompare(right)).map(([date, values]) => { const mastery = values.reduce((sum, point) => sum + point.mastery_score, 0) / values.length; return { date, skill_id: null, skill_name: "All Skills", mastery_score: mastery, mastery_percentage: Math.round(mastery * 100) }; });
    return [{ name: "All Skills", color: "#38bdf8", values: aggregate }];
  }, [points, selected]);
  const dates = useMemo(() => Array.from(new Set(points.map(point => point.date))).sort(), [points]);
  const x = (date: string): number => pad.l + Math.max(0, dates.indexOf(date)) / Math.max(1, dates.length - 1) * (width - pad.l - pad.r);
  const y = (score: number): number => pad.t + (1 - score) * (height - pad.t - pad.b);
  const smoothPath = (values: MasteryPoint[]): string => values.reduce((path, point, index) => { const px = x(point.date), py = y(point.mastery_score); if (!index) return `M${px},${py}`; const previous = values[index - 1]; const previousX = x(previous.date), previousY = y(previous.mastery_score), third = (px - previousX) / 3; return `${path} C${previousX + third},${previousY} ${px - third},${py} ${px},${py}`; }, "");
  return <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-indigo-300">Mastery history</p><h2 className="mt-2 text-xl font-bold">Skills over time</h2></div><select aria-label="Skill shown in mastery chart" value={selected} onChange={event => setSelected(event.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"><option value="all">All Skills</option>{names.map(name => <option key={name}>{name}</option>)}</select></div>
    <div ref={ref} className="mt-5 min-h-[280px] w-full">{width > 0 && <svg width={width} height={height} role="img" aria-label="Skill mastery line chart">{[0, 25, 50, 75, 100].map(value => <g key={value}><line x1={pad.l} x2={width - pad.r} y1={y(value / 100)} y2={y(value / 100)} stroke="#334155" strokeDasharray="3 4" /><text x={pad.l - 8} y={y(value / 100) + 4} textAnchor="end" fill="#64748b" fontSize="10">{value}%</text></g>)}{series.map(item => <g key={item.name}><path d={smoothPath(item.values)} fill="none" stroke={item.color} strokeWidth="2.5" />{item.values.map(point => <circle key={`${item.name}-${point.date}`} cx={x(point.date)} cy={y(point.mastery_score)} r="3" fill={item.color}><title>{item.name}: {point.mastery_percentage}% on {new Date(`${point.date}T12:00:00Z`).toLocaleDateString()}</title></circle>)}</g>)}{dates.filter((_, index) => index % 7 === 0 || index === dates.length - 1).map(date => <text key={date} x={x(date)} y={height - 8} textAnchor="middle" fill="#64748b" fontSize="9">{date.slice(5)}</text>)}</svg>}</div>
    <div className="mt-2 flex items-center justify-center gap-2 text-xs"><i className="h-2 w-2 rounded-full bg-sky-400" />{series[0]?.name ?? "All Skills"}</div>
  </section>;
}
