"use client";

import { useState } from "react";
import type { RoadmapItem as Item, RoadmapItemStatus } from "@/lib/roadmaps";

const icons: Record<Item["item_type"], string> = { lesson: "▤", exercise: "</>", project: "▱", assessment: "✓", review: "↻" };
const colors: Record<Item["item_type"], string> = { lesson: "text-blue-400", exercise: "text-purple-400", project: "text-orange-400", assessment: "text-red-400", review: "text-emerald-400" };

export function RoadmapItem({ item, locked, onOpen, onStatus }: { item: Item; locked: boolean; onOpen: () => void; onStatus: (status: RoadmapItemStatus) => void }): JSX.Element {
  const [menu, setMenu] = useState(false);
  const statusIcon = item.status === "completed" ? "✓" : item.status === "skipped" ? "−" : item.status === "active" ? "→" : "○";
  return <div className={`relative flex items-center gap-3 border-l-2 p-3 transition ${item.status === "completed" ? "border-emerald-400 bg-emerald-400/5" : "border-slate-700 bg-slate-950/40"}`}><button type="button" disabled={locked} onClick={onOpen} className="flex min-w-0 flex-1 items-center gap-3 text-left disabled:cursor-not-allowed"><span className={item.status === "completed" ? "text-emerald-400" : "text-slate-500"}>{statusIcon}</span><span className={`w-8 text-center text-xs font-bold ${colors[item.item_type]}`}>{icons[item.item_type]}</span><span className="min-w-0 flex-1"><span className="block text-[10px] font-bold uppercase tracking-wider text-slate-500">{item.item_type}</span><span className={`block truncate text-sm font-medium ${item.status === "completed" ? "text-slate-500 line-through" : ""}`}>{item.title}</span></span><span className="shrink-0 text-xs text-slate-500">{item.estimated_minutes ?? 0} min</span></button><button type="button" disabled={locked} onClick={() => setMenu((value) => !value)} className="rounded p-2 text-slate-500 hover:bg-slate-800 disabled:opacity-30" aria-label={`Actions for ${item.title}`}>•••</button>{menu && <div className="absolute right-2 top-12 z-20 w-40 rounded-xl border border-slate-700 bg-slate-900 p-1 shadow-xl">{[["Mark Complete", "completed"], ["Skip", "skipped"], ["Reset", "pending"]].map(([label, value]) => <button key={value} type="button" onClick={() => { onStatus(value as RoadmapItemStatus); setMenu(false); }} className="block w-full rounded-lg px-3 py-2 text-left text-xs hover:bg-slate-800">{label}</button>)}</div>}</div>;
}
