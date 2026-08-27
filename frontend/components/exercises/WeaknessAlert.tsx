"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import type { WeaknessPattern } from "@/lib/exercises";
import type { ConversationDetail, SendMessageResponse } from "@/lib/tutor";

export function WeaknessAlert({ skillId, skillName, skillSlug, pattern, wrongCount = 3, onError }: { skillId: string; skillName: string; skillSlug: string; pattern: WeaknessPattern; wrongCount?: number; onError: (message: string) => void }): JSX.Element | null {
  const key = `dismissed_weakness_${skillId}`; const router = useRouter();
  const [dismissed, setDismissed] = useState(() => typeof window !== "undefined" && Number(localStorage.getItem(key) ?? 0) >= wrongCount);
  if (dismissed) return null;
  const askTutor = async (): Promise<void> => { try { const conversation = await apiPost<ConversationDetail>("/api/v1/tutor/conversations", { skill_id: skillId }); await apiPost<SendMessageResponse>(`/api/v1/tutor/conversations/${conversation.id}/messages`, { content: `I am struggling with ${skillName}. My repeated misconception is: ${pattern.misconception}. Guide me through it.`, socratic_mode: true }); router.push(`/tutor/${conversation.id}`); } catch { onError("The tutor could not be opened. You can continue practicing here."); } };
  return <aside className="rounded-2xl border border-amber-400/30 bg-amber-400/5 p-5"><div className="flex items-start gap-3"><span className="text-xl">⚠</span><div className="flex-1"><h2 className="font-bold text-amber-200">Weakness Detected: {skillName}</h2><p className="mt-2 text-sm leading-6 text-slate-300">You&apos;ve missed {wrongCount} questions in a row. {pattern.misconception}</p><p className="mt-2 text-sm text-slate-500">{pattern.targeted_review}</p><div className="mt-4 flex flex-wrap gap-3"><button type="button" onClick={() => router.push(`/exercises/practice/${skillSlug}`)} className="rounded-lg bg-amber-400 px-3 py-2 text-xs font-bold text-slate-950">Practice This Now →</button><button type="button" onClick={() => void askTutor()} className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold">Ask Tutor to Explain →</button><button type="button" onClick={() => { localStorage.setItem(key, String(wrongCount)); setDismissed(true); }} className="px-2 text-xs text-slate-500">Dismiss</button></div></div></div></aside>;
}
