"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, apiGet } from "@/lib/api";
import type { AssessmentResults, AssessmentStatus } from "@/lib/assessments";
import type { GoalDetail } from "@/lib/goals";
import type { Roadmap } from "@/lib/roadmaps";
import type { DailyPlan, StreakInfo } from "@/lib/plans";
import { useAuth } from "@/lib/hooks/useAuth";

function greetingForHour(hour: number): string {
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
}

export default function DashboardPage(): JSX.Element {
  const { user } = useAuth();
  const [goal, setGoal] = useState<GoalDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [assessment, setAssessment] = useState<AssessmentStatus | null>(null);
  const [assessmentResults, setAssessmentResults] = useState<AssessmentResults | null>(null);
  const [assessmentChecked, setAssessmentChecked] = useState(false);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [todayPlan, setTodayPlan] = useState<DailyPlan | null>(null);
  const [streak, setStreak] = useState(0);
  const firstName = user?.full_name.trim().split(/\s+/)[0] || "Learner";

  useEffect(() => {
    let active = true;
    apiGet<GoalDetail>("/api/v1/goals/active")
      .then((result) => { if (active) setGoal(result); })
      .catch((reason: unknown) => {
        if (active && !(reason instanceof ApiError && reason.status === 404)) setError(true);
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!goal) return;
    let active = true;
    setAssessmentChecked(false);
    apiGet<AssessmentStatus>(`/api/v1/assessments/goal/${goal.id}`)
      .then(async (result) => {
        if (!active) return;
        setAssessment(result);
        if (result.status === "completed") {
          const profile = await apiGet<AssessmentResults>(`/api/v1/assessments/${result.id}/results`);
          if (active) setAssessmentResults(profile);
        }
      })
      .catch((reason: unknown) => { if (active && !(reason instanceof ApiError && reason.status === 404)) setError(true); })
      .finally(() => { if (active) setAssessmentChecked(true); });
    return () => { active = false; };
  }, [goal]);

  useEffect(() => {
    let active = true;
    Promise.all([apiGet<DailyPlan>("/api/v1/plans/today"), apiGet<StreakInfo>("/api/v1/plans/streak")])
      .then(([plan, streakInfo]) => { if (active) { setTodayPlan(plan); setStreak(streakInfo.current_streak); } })
      .catch((reason: unknown) => { if (active && !(reason instanceof ApiError && reason.status === 404)) setError(true); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!goal) return;
    let active = true;
    apiGet<Roadmap>(`/api/v1/roadmaps/goal/${goal.id}`)
      .then((value) => { if (active) setRoadmap(value); })
      .catch((reason: unknown) => { if (active && !(reason instanceof ApiError && reason.status === 404)) setError(true); });
    return () => { active = false; };
  }, [goal]);

  return (
    <div className="mx-auto max-w-7xl">
      <p className="text-sm font-medium text-sky-400">Your learning command center</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Good {greetingForHour(new Date().getHours())}, {firstName}!</h1>
      <p className="mt-2 text-slate-400">Here&apos;s where your personalized journey comes together.</p>

      {loading ? (
        <section className="mt-8 animate-pulse rounded-2xl border border-slate-800 bg-slate-900/60 p-7"><div className="h-4 w-28 rounded bg-slate-800" /><div className="mt-5 h-8 w-2/3 rounded bg-slate-800" /><div className="mt-5 h-4 w-1/2 rounded bg-slate-800" /><div className="mt-7 h-10 w-36 rounded bg-slate-800" /></section>
      ) : goal ? (
        <section className="mt-8 rounded-2xl border border-sky-400/25 bg-gradient-to-br from-sky-400/10 via-slate-900/70 to-indigo-500/10 p-7 sm:p-9">
          <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-center">
            <div className="max-w-3xl"><div className="flex flex-wrap gap-2"><span className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs font-semibold text-emerald-300">Active goal</span>{goal.estimated_weeks && <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">~{goal.estimated_weeks} weeks</span>}</div><h2 className="mt-4 text-2xl font-bold sm:text-3xl">{goal.title}</h2><p className="mt-3 text-sm text-slate-400">{goal.skill_count} skills · {goal.daily_study_minutes} minutes per day</p>{goal.ai_summary && <p className="mt-4 line-clamp-2 leading-7 text-slate-300">{goal.ai_summary}</p>}</div>
            <Link href={`/goal/${goal.id}`} className="shrink-0 rounded-xl bg-sky-400 px-6 py-3 text-center font-bold text-slate-950 transition hover:bg-sky-300">View Roadmap →</Link>
          </div>
        </section>
      ) : (
        <section className="mt-8 rounded-2xl border border-sky-400/20 bg-gradient-to-br from-sky-400/10 via-slate-900/60 to-indigo-500/10 p-8 text-center sm:p-12">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-400/10 text-sky-300"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" className="h-8 w-8"><path d="m2 9 10-5 10 5-10 5Z" /><path d="M6 11v5c3 3 9 3 12 0v-5M22 9v6" /></svg></div>
          <h2 className="mt-5 text-2xl font-bold">Let&apos;s set up your learning journey</h2>
          <p className="mx-auto mt-3 max-w-xl leading-7 text-slate-400">Tell us what you want to achieve and OpenAI will map the skills that take you there.</p>
          <Link href="/goal/new" className="mt-7 inline-block rounded-full bg-sky-400 px-6 py-3 font-semibold text-slate-950 transition hover:bg-sky-300">Set My Learning Goal →</Link>
        </section>
      )}

      {goal && assessmentChecked && assessment?.status !== "completed" && (
        <section className="mt-6 flex flex-col justify-between gap-5 rounded-2xl border border-amber-400/25 bg-amber-400/5 p-6 sm:flex-row sm:items-center">
          <div><p className="text-xs font-bold uppercase tracking-wider text-amber-300">Personalize your path</p><h2 className="mt-2 text-xl font-bold">Complete your skill assessment to get a personalized roadmap</h2><p className="mt-2 text-sm text-slate-400">It measures your starting point so familiar skills can move faster.</p></div>
          <Link href={assessment ? `/assessment/${assessment.id}` : `/goal/${goal.id}`} className="shrink-0 rounded-xl bg-amber-300 px-5 py-3 text-center font-bold text-slate-950">{assessment ? "Continue Assessment →" : "Start Assessment →"}</Link>
        </section>
      )}

      {goal && assessmentResults && (
        <section className="mt-6 rounded-2xl border border-emerald-400/20 bg-emerald-400/5 p-6">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center"><div><p className="text-xs font-bold uppercase tracking-wider text-emerald-300">Skill profile</p><h2 className="mt-2 text-2xl font-bold">Overall Knowledge Score: {Math.round(assessmentResults.overall_score)}%</h2></div><Link href={`/assessment/results/${assessmentResults.assessment_id}`} className="font-semibold text-emerald-300">View full results →</Link></div>
          <div className="mt-5 grid gap-5 sm:grid-cols-2"><div><p className="text-sm font-semibold text-slate-300">Strongest skills</p><div className="mt-2 flex flex-wrap gap-2">{assessmentResults.skill_scores.slice(0, 3).map((skill) => <span key={skill.skill_id} className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs text-emerald-200">{skill.skill_name} · {Math.round(skill.mastery_percentage)}%</span>)}</div></div><div><p className="text-sm font-semibold text-slate-300">Focus areas</p><div className="mt-2 flex flex-wrap gap-2">{[...assessmentResults.skill_scores].sort((left, right) => left.mastery_score - right.mastery_score).slice(0, 3).map((skill) => <span key={skill.skill_id} className="rounded-full bg-amber-400/10 px-3 py-1 text-xs text-amber-200">{skill.skill_name} · {Math.round(skill.mastery_percentage)}%</span>)}</div></div></div>
        </section>
      )}

      {roadmap && (() => {
        const activePhase = roadmap.phases.find((phase) => phase.status === "active");
        const nextItems = activePhase?.items.filter((item) => item.status === "pending").slice(0, 2) ?? [];
        return <section className="mt-6 rounded-2xl border border-indigo-400/20 bg-slate-900/60 p-6 sm:p-7"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start"><div><p className="text-xs font-bold uppercase tracking-wider text-indigo-300">Your Roadmap Progress</p><h2 className="mt-2 text-xl font-bold">{activePhase ? `Current Phase: ${activePhase.title}` : "Roadmap complete"}</h2></div><Link href="/roadmap" className="font-semibold text-sky-300">View Full Roadmap →</Link></div><div className="mt-5 flex items-center gap-3"><div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-800"><div className="h-full rounded-full bg-gradient-to-r from-indigo-400 to-sky-400" style={{ width: `${roadmap.overall_progress_percentage}%` }} /></div><span className="text-sm font-bold">{Math.round(roadmap.overall_progress_percentage)}%</span></div><p className="mt-2 text-xs text-slate-500">{roadmap.completed_items} of {roadmap.total_items} items completed</p>{nextItems.length > 0 && <div className="mt-5 grid gap-3 sm:grid-cols-2">{nextItems.map((item) => <div key={item.id} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4"><p className="text-xs font-bold uppercase text-slate-500">Next up · {item.item_type}</p><p className="mt-2 truncate font-semibold">{item.title}</p><p className="mt-1 text-xs text-slate-500">{item.estimated_minutes ?? 0} min</p></div>)}</div>}</section>;
      })()}

      {todayPlan && <section className="mt-6 rounded-2xl border border-sky-400/20 bg-slate-900/60 p-6 sm:p-7"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start"><div><p className="text-xs font-bold uppercase tracking-wider text-sky-300">Today&apos;s Learning Plan</p><h2 className="mt-2 text-xl font-bold">{todayPlan.status === "completed" ? "✅ Plan complete! See you tomorrow." : `${todayPlan.completed_items_count} of ${todayPlan.total_items_count} tasks complete`}</h2></div><Link href="/plan" className="font-semibold text-sky-300">Open Full Plan →</Link></div><div className="mt-5 grid gap-2">{todayPlan.items.slice(0, 5).map((item) => <div key={item.id} className="flex items-center gap-3 text-sm"><span className={item.status === "completed" ? "text-emerald-400" : item.status === "in_progress" ? "text-sky-400" : "text-slate-600"}>{item.status === "completed" ? "✓" : item.status === "in_progress" ? "▶" : item.status === "skipped" ? "−" : "○"}</span><span className={`min-w-0 flex-1 truncate ${item.status === "completed" ? "text-slate-500 line-through" : "text-slate-300"}`}>{item.title}</span><span className="text-xs text-slate-600">{item.estimated_minutes}m</span></div>)}</div><p className="mt-4 text-xs text-slate-500">{todayPlan.total_estimated_minutes} min total · 🔥 {streak}-day streak</p></section>}

      {error && <p className="mt-4 rounded-xl border border-amber-400/20 bg-amber-400/5 px-4 py-3 text-sm text-amber-200">We couldn&apos;t refresh your active goal. The rest of your dashboard is still available.</p>}

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"><p className="text-sm text-slate-400">Current Goal</p><p className="mt-3 text-xl font-semibold">{goal ? "In progress" : "Not set yet"}</p></article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"><p className="text-sm text-slate-400">Today&apos;s Tasks</p><p className="mt-3 text-xl font-semibold">{todayPlan ? `${todayPlan.completed_items_count}/${todayPlan.total_items_count} complete` : "No plan yet"}</p></article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"><p className="text-sm text-slate-400">Learning Streak</p><p className="mt-3 text-xl font-semibold">{streak} days 🔥</p></article>
      </section>
    </div>
  );
}
