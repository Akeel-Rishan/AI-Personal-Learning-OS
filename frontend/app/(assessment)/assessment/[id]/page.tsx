"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { AssessmentShell } from "@/components/assessment/AssessmentShell";
import { QuestionCard } from "@/components/assessment/QuestionCard";
import { ApiError, apiGet, apiPost } from "@/lib/api";
import type { AnswerFeedback, AssessmentQuestion, AssessmentStatus } from "@/lib/assessments";

interface SavedState { startedAt: number; questionId?: string; answer?: string }

export default function AssessmentPage(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const key = `assessment:${id}`;
  const submittingRef = useRef(false);
  const [status, setStatus] = useState<AssessmentStatus | null>(null);
  const [question, setQuestion] = useState<AssessmentQuestion | null>(null);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  const [nextReady, setNextReady] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [transitioning, setTransitioning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [startedAt, setStartedAt] = useState(Date.now());
  const [questionStartedAt, setQuestionStartedAt] = useState(Date.now());
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    let saved: SavedState | null = null;
    try { saved = JSON.parse(sessionStorage.getItem(key) ?? "null") as SavedState | null; } catch { saved = null; }
    const restoredStart = saved?.startedAt ?? Date.now();
    setStartedAt(restoredStart);
    let active = true;
    apiGet<AssessmentStatus>(`/api/v1/assessments/${id}`).then((result) => {
      if (!active) return;
      if (result.status === "completed") { router.replace(`/assessment/results/${id}`); return; }
      const current = result.current_question ?? result.next_question;
      setStatus(result); setQuestion(current);
      if (current && saved?.questionId === current.id) setAnswer(saved.answer ?? "");
      sessionStorage.setItem(key, JSON.stringify({ startedAt: restoredStart, questionId: current?.id, answer: saved?.questionId === current?.id ? (saved?.answer ?? "") : "" }));
    }).catch((reason: unknown) => {
      if (!active) return;
      if (reason instanceof ApiError && [401, 403, 404].includes(reason.status)) router.replace("/dashboard");
      else setError("We couldn't load this assessment. Check that the backend is running, then try again.");
    });
    return () => { active = false; };
  }, [id, key, router]);

  useEffect(() => {
    const update = (): void => setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    update(); const interval = window.setInterval(update, 1000); return () => window.clearInterval(interval);
  }, [startedAt]);

  useEffect(() => {
    if (!question) return;
    sessionStorage.setItem(key, JSON.stringify({ startedAt, questionId: question.id, answer }));
  }, [answer, key, question, startedAt]);

  const valid = question?.question_type === "explanation" ? answer.trim().length >= 20 : answer.trim().length > 0;

  const submit = useCallback(async (skip = false): Promise<void> => {
    if (!question || submittingRef.current || feedback || (!skip && !valid)) return;
    submittingRef.current = true; setSubmitting(true); setError(null);
    try {
      const result = await apiPost<AnswerFeedback>(`/api/v1/assessments/${id}/answer`, { question_id: question.id, user_answer: skip ? "" : answer, time_spent_seconds: Math.max(0, Math.floor((Date.now() - questionStartedAt) / 1000)) });
      setFeedback(result); setStatus((current) => current ? { ...current, completed_questions: result.completed_questions } : current);
      window.setTimeout(() => setNextReady(true), 2000);
    } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Your answer could not be submitted."); }
    finally { submittingRef.current = false; setSubmitting(false); }
  }, [answer, feedback, id, question, questionStartedAt, valid]);

  const next = (): void => {
    if (!feedback || !nextReady) return;
    if (feedback.is_assessment_complete) { sessionStorage.removeItem(key); window.dispatchEvent(new Event("learning-progress-updated")); router.push(`/assessment/results/${id}`); return; }
    setTransitioning(true);
    window.setTimeout(() => { setQuestion(feedback.next_question); setAnswer(""); setFeedback(null); setNextReady(false); setQuestionStartedAt(Date.now()); setTransitioning(false); }, 250);
  };

  if (error && !status) return <main className="flex min-h-screen items-center justify-center bg-slate-950 p-5 text-slate-100"><div className="max-w-md rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center"><h1 className="text-xl font-bold">Assessment unavailable</h1><p className="mt-3 text-slate-400">{error}</p><button type="button" onClick={() => window.location.reload()} className="mt-6 rounded-xl bg-sky-400 px-5 py-3 font-bold text-slate-950">Try again</button></div></main>;
  if (!status || !question) return <main className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-400"><div className="text-center"><span className="mx-auto block h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-sky-400" /><p className="mt-4">Preparing your next question...</p></div></main>;

  return <AssessmentShell goalTitle={status.goal_title ?? "Your Goal"} completed={status.completed_questions} total={status.total_questions} elapsedSeconds={elapsedSeconds} canSubmit={valid} isSubmitting={submitting} feedbackVisible={Boolean(feedback)} onSkip={() => void submit(true)} onSubmit={() => void submit()}><QuestionCard question={question} questionNumber={status.completed_questions + (feedback ? 0 : 1)} answer={answer} onAnswer={setAnswer} onSubmit={() => void submit()} feedback={feedback} nextReady={nextReady} onNext={next} transitioning={transitioning} />{error && <p className="mt-4 rounded-xl border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-200">{error}</p>}</AssessmentShell>;
}
