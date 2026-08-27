"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import type { AttemptFeedback, Exercise } from "@/lib/exercises";
import type { ConversationDetail, SendMessageResponse } from "@/lib/tutor";

export function FeedbackPanel({ exercise, feedback, onError }: { exercise: Exercise; feedback: AttemptFeedback; onError: (message: string) => void }): JSX.Element {
  const router = useRouter(); const [openingTutor, setOpeningTutor] = useState(false); const [showBetter, setShowBetter] = useState(false);
  const review = feedback.detailed_feedback as any;
  const improvements: Array<any> = review?.improvements ?? [];
  const askTutor = async (): Promise<void> => {
    setOpeningTutor(true);
    try {
      const conversation = await apiPost<ConversationDetail>("/api/v1/tutor/conversations", { skill_id: exercise.skill_id });
      const issue = improvements[0]?.issue ?? feedback.feedback;
      await apiPost<SendMessageResponse>(`/api/v1/tutor/conversations/${conversation.id}/messages`, { content: `I just did an exercise on ${exercise.skill_name ?? "this skill"} and got feedback that ${issue}. Can you help me understand this better?`, socratic_mode: true });
      router.push(`/tutor/${conversation.id}`);
    } catch { onError("The tutor conversation could not be created. Your exercise progress is safe."); setOpeningTutor(false); }
  };
  return <section className={`mt-6 rounded-2xl border p-5 sm:p-6 ${feedback.is_correct ? "border-emerald-400/30 bg-emerald-400/5" : "border-amber-400/30 bg-amber-400/5"}`}><div className="flex flex-wrap items-center justify-between gap-3"><div><p className={`text-xl font-black ${feedback.is_correct ? "text-emerald-300" : "text-amber-300"}`}>{feedback.is_correct ? "✓ Correct!" : "Keep working"}</p><p className="mt-1 text-sm text-slate-400">Score: {Math.round(feedback.score * 100)}% · Mastery {feedback.mastery_change >= 0 ? "+" : ""}{Math.round(feedback.mastery_change * 100)}%</p></div>{review?.passed_test_cases != null && <span className="rounded-full bg-slate-950 px-3 py-1.5 text-xs">Passed {review.passed_test_cases}/{review.total_test_cases} tests</span>}</div><p className="mt-4 leading-7 text-slate-300">{feedback.feedback}</p>{review?.strengths?.length > 0 && <div className="mt-5"><h3 className="font-bold text-emerald-300">✓ Strengths</h3><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">{review.strengths.map((item: string) => <li key={item}>{item}</li>)}</ul></div>}{improvements.length > 0 && <div className="mt-5"><h3 className="font-bold text-amber-300">💡 Improvements</h3><div className="mt-2 space-y-3">{improvements.map((item, index) => <article key={index} className="rounded-xl border border-slate-800 bg-slate-950/60 p-4"><span className="text-[10px] font-bold uppercase text-amber-400">{item.severity ?? "suggestion"}</span><p className="mt-1 font-semibold">{item.issue}</p><p className="mt-2 text-sm leading-6 text-slate-400">{item.suggestion}</p>{item.example && <code className="mt-2 block overflow-x-auto rounded bg-[#1e1e1e] p-3 text-xs text-sky-200">{item.example}</code>}</article>)}</div></div>}{review?.learning_note && <div className="mt-5 rounded-xl bg-indigo-400/10 p-4"><p className="text-xs font-bold uppercase text-indigo-300">Learning Note</p><p className="mt-2 text-sm leading-6 text-slate-300">{review.learning_note}</p></div>}<div className="mt-5 flex flex-wrap gap-3">{review?.better_approach && <button type="button" onClick={() => setShowBetter((value) => !value)} className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-semibold">{showBetter ? "Hide" : "See"} Better Approach</button>}<button type="button" disabled={openingTutor} onClick={() => void askTutor()} className="rounded-lg bg-sky-400 px-4 py-2 text-sm font-bold text-slate-950 disabled:opacity-50">{openingTutor ? "Opening Tutor..." : "Ask Tutor →"}</button></div>{showBetter && <p className="mt-4 rounded-xl bg-slate-950 p-4 text-sm leading-7 text-slate-300">{review.better_approach}</p>}</section>;
}
