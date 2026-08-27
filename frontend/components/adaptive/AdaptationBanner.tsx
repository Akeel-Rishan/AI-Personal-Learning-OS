"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { dismissAdaptiveNotification, getAdaptiveNotifications, type InterventionNotification } from "@/lib/adaptive";
import { GapSeverityBadge } from "./GapSeverityBadge";

let notificationCache: InterventionNotification[] | null = null;
let notificationCacheTime = 0;
const CACHE_MS = 5 * 60 * 1000;

export function AdaptationBanner(): JSX.Element | null {
  const [items, setItems] = useState<InterventionNotification[]>(notificationCache || []);

  useEffect(() => {
    let active = true;
    async function load(force = false): Promise<void> {
      if (!force && notificationCache && Date.now() - notificationCacheTime < CACHE_MS) { setItems(notificationCache); return; }
      try { const value = (await getAdaptiveNotifications()).filter((item) => !localStorage.getItem(`dismissed_adaptation_${item.gap_id}`)); notificationCache = value; notificationCacheTime = Date.now(); if (active) setItems(value); } catch { /* A banner must never block the workspace. */ }
    }
    void load();
    const refresh = () => void load(true);
    const timer = window.setInterval(refresh, CACHE_MS);
    window.addEventListener("adaptive-learning-updated", refresh);
    return () => { active = false; window.clearInterval(timer); window.removeEventListener("adaptive-learning-updated", refresh); };
  }, []);

  const item = items[0];
  if (!item) return null;
  async function dismiss(): Promise<void> {
    localStorage.setItem(`dismissed_adaptation_${item.gap_id}`, new Date().toISOString());
    setItems((current) => current.filter((entry) => entry.gap_id !== item.gap_id));
    notificationCache = (notificationCache || []).filter((entry) => entry.gap_id !== item.gap_id);
    try { await dismissAdaptiveNotification(item.gap_id); } catch { /* Local dismissal remains effective for this session. */ }
  }
  return <aside className="mb-6 rounded-2xl border border-orange-400/25 bg-gradient-to-r from-orange-400/10 to-sky-400/5 p-4"><div className="flex items-start gap-4"><div className="mt-1 text-xl">⚡</div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h2 className="font-bold">Your learning path adapted</h2><GapSeverityBadge severity={item.severity} /></div><p className="mt-1 text-sm text-slate-300">{item.learner_message}</p><p className="mt-2 text-xs text-slate-500">About {item.estimated_fix_minutes} minutes · {item.intervention_items_count} targeted activities</p><div className="mt-3 flex flex-wrap gap-2"><Link href="/gaps" className="rounded-lg bg-orange-300 px-3 py-1.5 text-xs font-bold text-slate-950">Review changes</Link>{item.tutor_conversation_id && <Link href={`/tutor/${item.tutor_conversation_id}`} className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs font-semibold">Ask tutor</Link>}</div></div><button type="button" onClick={() => void dismiss()} aria-label="Dismiss adaptation" className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800">✕</button></div></aside>;
}
