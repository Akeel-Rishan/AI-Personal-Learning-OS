"use client";

import type { AnswerFeedback, AssessmentQuestion } from "@/lib/assessments";
import { CodeQuestion } from "@/components/assessment/CodeQuestion";
import { MCQQuestion } from "@/components/assessment/MCQQuestion";
import { TextQuestion } from "@/components/assessment/TextQuestion";

interface Props {
  question: AssessmentQuestion;
  questionNumber: number;
  answer: string;
  onAnswer: (value: string) => void;
  onSubmit: () => void;
  feedback: AnswerFeedback | null;
  nextReady: boolean;
  onNext: () => void;
  transitioning: boolean;
}

export function QuestionCard({ question, questionNumber, answer, onAnswer, onSubmit, feedback, nextReady, onNext, transitioning }: Props): JSX.Element {
  const parts = question.question_text.split("\n");
  const prompt = question.question_type === "debugging" || question.question_type === "coding" ? parts[0] : question.question_text;
  const code = parts.length > 1 ? parts.slice(1).join("\n").trim() : "";
  return (
    <article className={`rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-2xl shadow-black/20 transition duration-300 sm:p-8 ${transitioning ? "translate-y-1 opacity-0" : "opacity-100"}`}>
      <div className="flex items-center justify-between gap-4"><span className="rounded-full border border-sky-400/25 bg-sky-400/10 px-3 py-1 text-xs font-semibold text-sky-300">{question.skill_name}</span><span className="flex gap-1" title={`Difficulty ${question.difficulty} of 5`}>{Array.from({ length: 5 }, (_, index) => <i key={index} className={`h-2 w-2 rounded-full ${index < question.difficulty ? "bg-amber-400" : "bg-slate-700"}`} />)}</span></div>
      <p className="mt-6 text-xs font-bold uppercase tracking-[0.2em] text-slate-500">Question {questionNumber}</p>
      <h1 className="mt-3 whitespace-pre-wrap text-xl font-semibold leading-8 sm:text-2xl">{prompt}</h1>
      <div className="mt-7">
        {question.question_type === "multiple_choice" && <MCQQuestion options={question.options ?? []} value={answer} onChange={onAnswer} onSubmit={onSubmit} disabled={Boolean(feedback)} feedback={feedback} />}
        {question.question_type === "explanation" && <TextQuestion value={answer} onChange={onAnswer} disabled={Boolean(feedback)} />}
        {(question.question_type === "debugging" || question.question_type === "coding") && <CodeQuestion code={code} value={answer} onChange={onAnswer} disabled={Boolean(feedback)} />}
      </div>
      {feedback && <section className={`mt-7 animate-feedback-in rounded-xl border p-5 ${feedback.is_correct ? "border-emerald-400/40 bg-emerald-400/10" : "border-red-400/40 bg-red-400/10"}`}><div className="flex gap-3"><span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full font-bold ${feedback.is_correct ? "bg-emerald-400 text-slate-950" : "bg-red-400 text-white"}`}>{feedback.is_correct ? "✓" : "×"}</span><div><h2 className="font-bold">{feedback.is_correct ? "Nice work" : "Keep building"}</h2><p className="mt-2 leading-7 text-slate-300">{feedback.feedback}</p>{!feedback.is_correct && <div className="mt-4 rounded-lg bg-slate-950/60 p-3"><p className="text-xs font-bold uppercase tracking-wider text-slate-500">Reference answer</p><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-300">{feedback.correct_answer}</p></div>}</div></div><button type="button" disabled={!nextReady} onClick={onNext} className="mt-5 w-full rounded-xl bg-slate-100 px-5 py-3 font-bold text-slate-950 transition hover:bg-white disabled:cursor-wait disabled:opacity-50">{nextReady ? (feedback.is_assessment_complete ? "See My Results →" : "Next Question →") : "Reviewing feedback..."}</button></section>}
    </article>
  );
}
