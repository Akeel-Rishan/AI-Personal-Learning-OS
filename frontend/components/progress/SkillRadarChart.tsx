"use client";
import { useMemo } from "react";
import type { CategoryBreakdown } from "@/lib/progress";
import { useChartSize } from "./useChartSize";

export function SkillRadarChart({ categories }: { categories: CategoryBreakdown[] }): JSX.Element {
  const { ref, width } = useChartSize(); const size=Math.min(width,360); const c=size/2; const radius=Math.max(40,size/2-58);
  const values=useMemo(()=>categories.slice(0,8),[categories]);
  const point=(i:number, scale:number)=>{const a=-Math.PI/2+(i*Math.PI*2/Math.max(1,values.length));return [c+Math.cos(a)*radius*scale,c+Math.sin(a)*radius*scale]};
  const polygon=(scale:number)=>values.map((_,i)=>point(i,scale).join(",")).join(" ");
  return <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"><p className="text-xs font-bold uppercase tracking-wider text-purple-300">Category balance</p><h2 className="mt-2 text-xl font-bold">Skill radar</h2><div ref={ref} className="mt-4 flex min-h-[300px] justify-center">{size>0&&values.length>=3?<svg width={size} height={size} role="img" aria-label="Skill category radar chart">{[.25,.5,.75,1].map(n=><polygon key={n} points={polygon(n)} fill="none" stroke="#334155"/>)}{values.map((_,i)=>{const [x,y]=point(i,1);return <line key={i} x1={c} y1={c} x2={x} y2={y} stroke="#334155"/>})}<polygon points={values.map((v,i)=>point(i,v.average_mastery).join(",")).join(" ")} fill="rgba(56,189,248,.2)" stroke="#38bdf8" strokeWidth="2"/>{values.map((v,i)=>{const [x,y]=point(i,1.17);return <text key={v.category} x={x} y={y} textAnchor="middle" dominantBaseline="middle" fill="#cbd5e1" fontSize="10">{v.category} {v.mastery_percentage}%</text>})}</svg>:<p className="self-center text-sm text-slate-500">Track skills in at least three categories to unlock the radar.</p>}</div></section>;
}
