"use client";

import { useEffect, useRef } from "react";
import type { RoadmapItem, RoadmapItemStatus } from "@/lib/roadmaps";

interface Props { item: RoadmapItem | null; onClose: () => void; onStatus: (status: RoadmapItemStatus) => void; onPrevious: () => void; onNext: () => void; hasPrevious: boolean; hasNext: boolean; }

export function ItemDrawer({ item, onClose, onStatus, onPrevious, onNext, hasPrevious, hasNext }: Props): JSX.Element {
  const drawer = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!item) return;
    const previous = document.activeElement as HTMLElement | null;
    drawer.current?.focus();
    const keydown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") onClose();
      if (event.key !== "Tab" || !drawer.current) return;
      const controls = Array.from(drawer.current.querySelectorAll<HTMLElement>('button, [href], [tabindex]:not([tabindex="-1"])')).filter((control) => !control.hasAttribute("disabled"));
      if (!controls.length) return;
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", keydown);
    return () => { document.removeEventListener("keydown", keydown); previous?.focus(); };
  }, [item, onClose]);
  return <div className={`fixed inset-0 z-50 transition ${item ? "pointer-events-auto" : "pointer-events-none"}`} aria-hidden={!item}><button type="button" onClick={onClose} className={`absolute inset-0 bg-black/70 transition-opacity ${item ? "opacity-100" : "opacity-0"}`} aria-label="Close item details" /><aside ref={drawer} tabIndex={-1} role="dialog" aria-modal="true" aria-label={item?.title ?? "Roadmap item"} className={`absolute inset-y-0 right-0 w-full overflow-y-auto border-l border-slate-800 bg-slate-950 p-6 shadow-2xl outline-none transition-transform duration-300 sm:w-[400px] ${item ? "translate-x-0" : "translate-x-full"}`}>{item && <><div className="flex items-start justify-between gap-4"><div><div className="flex flex-wrap gap-2"><span className="rounded-full bg-sky-400/10 px-3 py-1 text-xs font-bold capitalize text-sky-300">{item.item_type}</span>{item.skill_name && <span className="rounded-full bg-indigo-400/10 px-3 py-1 text-xs text-indigo-200">{item.skill_name}</span>}</div><h2 className="mt-4 text-2xl font-bold leading-8">{item.title}</h2></div><button type="button" onClick={onClose} className="rounded-lg p-2 text-xl text-slate-500 hover:bg-slate-800" aria-label="Close">×</button></div><p className="mt-4 text-sm text-slate-500">About {item.estimated_minutes ?? 0} minutes</p><p className="mt-7 leading-7 text-slate-300">{item.description ?? `Build practical confidence through this ${item.item_type}.`}</p><section className="mt-8"><h3 className="font-bold">What you&apos;ll learn</h3><ul className="mt-3 space-y-3 text-sm leading-6 text-slate-400">{[`The core ideas behind ${item.skill_name ?? "this skill"}`, "How to apply the concept in realistic situations", "Common mistakes and how to avoid them", "How this skill supports later roadmap phases"].map((text) => <li key={text} className="flex gap-3"><span className="text-sky-400">✓</span>{text}</li>)}</ul></section><div className="mt-8 space-y-3"><button type="button" onClick={() => onStatus("completed")} className="w-full rounded-xl bg-sky-400 px-5 py-3 font-bold text-slate-950">{item.status === "pending" ? "Start Learning" : "Mark Complete"}</button><button type="button" onClick={() => onStatus("completed")} className="w-full rounded-xl border border-emerald-400/30 px-5 py-3 font-bold text-emerald-300">Mark Complete</button><button type="button" onClick={() => onStatus("skipped")} className="w-full rounded-xl px-5 py-3 text-sm font-semibold text-slate-500 hover:bg-slate-900">Skip for Now</button></div><nav className="mt-10 flex justify-between border-t border-slate-800 pt-5"><button type="button" disabled={!hasPrevious} onClick={onPrevious} className="text-sm font-semibold text-sky-300 disabled:text-slate-700">← Previous Item</button><button type="button" disabled={!hasNext} onClick={onNext} className="text-sm font-semibold text-sky-300 disabled:text-slate-700">Next Item →</button></nav></>}</aside></div>;
}
