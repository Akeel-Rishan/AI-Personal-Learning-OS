"use client";
import { useMemo } from "react";
import type { HeatmapDay } from "@/lib/progress";
import { useChartSize } from "./useChartSize";

export function StreakCalendar({ days }: { days: HeatmapDay[] }): JSX.Element {
  const { ref, width } = useChartSize(0); const visible = useMemo(() => width > 0 && width < 640 ? days.slice(-84) : days, [days, width]);
  const colors = ["bg-slate-800", "bg-sky-950", "bg-sky-800", "bg-sky-500", "bg-cyan-300"];
  const months = useMemo(() => visible.filter((day, index) => index % 28 === 0).map(day => new Date(`${day.date}T12:00:00Z`).toLocaleDateString(undefined, { month: "short" })), [visible]);
  return <section ref={ref} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"><div className="flex justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-wider text-emerald-300">Consistency</p><h2 className="mt-2 text-xl font-bold">Learning activity</h2></div><p className="text-xs text-slate-500">Last {visible.length / 7 || 26} weeks</p></div>
    <div className="mt-5 overflow-x-auto pb-2"><div className="ml-8 flex min-w-[340px] justify-between pr-2 text-[10px] text-slate-500">{months.map((month, index) => <span key={`${month}-${index}`}>{month}</span>)}</div><div className="mt-1 flex min-w-[340px] gap-2"><div className="grid h-[122px] w-6 grid-rows-7 text-[9px] text-slate-600"><span /><span>Mon</span><span /><span>Wed</span><span /><span>Fri</span><span /></div><div className="grid flex-1 grid-flow-col grid-rows-7 gap-1">{visible.map(day => <div key={day.date} className={`h-3.5 min-w-3.5 rounded-sm ${colors[Math.min(4, day.intensity)]}`} title={`${new Date(`${day.date}T12:00:00Z`).toLocaleDateString()}: ${day.completed_items} items completed, ${day.study_minutes} minutes studied`} />)}</div></div></div>
    <div className="mt-3 flex items-center justify-end gap-1 text-[10px] text-slate-500"><span>None</span>{colors.map((color, index) => <i key={index} className={`h-3 w-3 rounded-sm ${color}`} />)}<span>Excellent</span></div></section>;
}
