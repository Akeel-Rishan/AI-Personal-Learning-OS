"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { getMyProjects } from "@/lib/projects";
import type { UserProject } from "@/lib/projects";

export function ProjectDashboardWidget(): JSX.Element {
  const [items, setItems] = useState<UserProject[]>([]); const [loaded, setLoaded] = useState(false);
  useEffect(() => { let active = true; getMyProjects("active").then((value) => { if (active) setItems(value.slice(0, 2)); }).catch(() => undefined).finally(() => { if (active) setLoaded(true); }); return () => { active = false; }; }, []);
  return <section className="rounded-2xl border border-indigo-400/20 bg-indigo-400/5 p-5"><div className="flex justify-between"><h2 className="font-bold">Active Projects</h2><Link href="/projects" className="text-sm text-sky-300">Browse projects →</Link></div>{loaded && items.length === 0 ? <div className="mt-4 rounded-xl border border-dashed border-slate-700 p-5 text-center"><p className="text-sm text-slate-400">Turn your learning into a portfolio-ready build.</p><Link href="/projects" className="mt-3 inline-block rounded-lg bg-indigo-400 px-4 py-2 text-sm font-bold text-slate-950">Start your first project →</Link></div> : <div className="mt-4 grid gap-3 md:grid-cols-2">{items.map((item) => <Link key={item.id} href={`/projects/workspace/${item.id}`} className="rounded-xl border border-slate-800 bg-slate-950/40 p-4"><b>{item.project.title}</b><div className="mt-3 h-2 rounded bg-slate-800"><div className="h-full rounded bg-indigo-400" style={{ width: `${item.progress_percentage}%` }} /></div><p className="mt-2 text-xs text-slate-500">Stage {Math.min(item.current_stage_index + 1, item.total_stages)} of {item.total_stages} · {item.progress_percentage}%</p></Link>)}</div>}</section>;
}
