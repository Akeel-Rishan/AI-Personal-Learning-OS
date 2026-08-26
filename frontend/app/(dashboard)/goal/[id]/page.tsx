"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, apiGet, apiPost } from "@/lib/api";
import type { AssessmentStatus } from "@/lib/assessments";
import type { GoalDetail } from "@/lib/goals";
import { SkillGraph } from "@/components/skill/SkillGraph";

function formatDate(value: string | null): string {
  if (!value) return "Flexible timeline";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "long" }).format(new Date(`${value}T00:00:00`));
}

export default function GoalDetailPage(): JSX.Element {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [goal, setGoal] = useState<GoalDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [assessmentError, setAssessmentError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const startAssessment = async (): Promise<void> => {
    if (generating) return;
    setGenerating(true);
    setAssessmentError(null);
    try {
      const assessment = await apiPost<AssessmentStatus>("/api/v1/assessments/", { goal_id: params.id });
      router.push(assessment.status === "completed" ? `/assessment/results/${assessment.id}` : `/assessment/${assessment.id}`);
    } catch (reason) {
      setAssessmentError(reason instanceof ApiError ? reason.message : "Your assessment could not be generated.");
      setGenerating(false);
    }
  };

  useEffect(() => {
    let active = true;
    apiGet<GoalDetail>(`/api/v1/goals/${params.id}`)
      .then((result) => { if (active) setGoal(result); })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof ApiError && reason.status === 404 ? "This goal could not be found." : "We couldn't load this roadmap. Please try again.");
      });
    return () => { active = false; };
  }, [params.id]);

  if (error) return <div className="mx-auto max-w-4xl rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center"><h1 className="text-2xl font-bold">Roadmap unavailable</h1><p className="mt-3 text-slate-400">{error}</p><Link href="/dashboard" className="mt-6 inline-block font-semibold text-sky-400">Back to dashboard →</Link></div>;
  if (!goal) return <div className="mx-auto max-w-7xl animate-pulse"><div className="h-8 w-2/3 rounded bg-slate-800" /><div className="mt-4 h-5 w-1/3 rounded bg-slate-900" /><div className="mt-8 h-32 rounded-2xl bg-slate-900" /><div className="mt-6 h-[420px] rounded-2xl bg-slate-900" /></div>;

  return (
    <div className="mx-auto max-w-7xl">
      <Link href="/dashboard" className="text-sm font-semibold text-slate-500 transition hover:text-sky-300">← Dashboard</Link>
      <div className="mt-5 flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-1 text-xs font-semibold capitalize text-emerald-300">{goal.status}</span>
            {goal.difficulty_assessment && <span className="rounded-full border border-indigo-400/25 bg-indigo-400/10 px-3 py-1 text-xs font-semibold capitalize text-indigo-300">{goal.difficulty_assessment}</span>}
          </div>
          <h1 className="mt-4 max-w-4xl text-3xl font-bold tracking-tight sm:text-4xl">{goal.title}</h1>
          <p className="mt-3 text-sm text-slate-400">{formatDate(goal.target_date)} · {goal.daily_study_minutes} minutes per day · {goal.skill_count} skills</p>
        </div>
        <button type="button" disabled={generating} onClick={() => void startAssessment()} className="rounded-xl bg-sky-400 px-6 py-3 font-bold text-slate-950 transition hover:bg-sky-300 disabled:cursor-wait disabled:opacity-70">{generating ? "Generating your assessment..." : "Assess My Knowledge →"}</button>
      </div>

      {generating && <div className="mt-5 rounded-xl border border-sky-400/20 bg-sky-400/5 px-4 py-3 text-sm text-sky-200"><span className="mr-3 inline-block h-4 w-4 animate-spin rounded-full border-2 border-sky-900 border-t-sky-300 align-[-3px]" />Selecting questions across your foundational skills. This can take a moment.</div>}
      {assessmentError && <p className="mt-5 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-200">{assessmentError}</p>}

      <section className="mt-8 rounded-2xl border border-sky-400/20 bg-gradient-to-br from-sky-400/10 via-slate-900/70 to-indigo-500/10 p-6 sm:p-8">
        <div className="flex flex-wrap gap-2"><span className="rounded-full bg-sky-300 px-3 py-1 text-xs font-bold text-slate-950">~{goal.estimated_weeks ?? "—"} weeks</span><span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">AI-designed path</span></div>
        <p className="mt-5 max-w-5xl text-lg leading-8 text-slate-200">{goal.ai_summary ?? "Your skill path is ready to explore."}</p>
      </section>

      <section className="mt-8">
        <div className="mb-4"><h2 className="text-2xl font-bold">Skill dependency graph</h2><p className="mt-1 text-sm text-slate-500">Prerequisites flow from left to right.</p></div>
        <SkillGraph skills={goal.required_skills} />
      </section>

      <section className="mt-9 overflow-hidden rounded-2xl border border-slate-800">
        <div className="border-b border-slate-800 bg-slate-900/80 px-5 py-4"><h2 className="font-bold">Required skills</h2></div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[620px] text-left text-sm">
            <thead className="bg-slate-950/60 text-xs uppercase tracking-wider text-slate-500"><tr><th className="px-5 py-3">Order</th><th className="px-5 py-3">Skill</th><th className="px-5 py-3">Category</th><th className="px-5 py-3">Hours</th><th className="px-5 py-3">Type</th></tr></thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/40">
              {[...goal.required_skills].sort((left, right) => left.priority_order - right.priority_order).map((item) => <tr key={item.skill.id}><td className="px-5 py-4 font-bold text-sky-300">{item.priority_order}</td><td className="px-5 py-4 font-semibold">{item.skill.name}</td><td className="px-5 py-4 capitalize text-slate-400">{item.skill.category.replace("-", " ")}</td><td className="px-5 py-4 text-slate-400">{item.skill.estimated_hours ?? 0}h</td><td className="px-5 py-4"><span className={`rounded-full px-2 py-1 text-xs ${item.is_required ? "bg-rose-400/10 text-rose-300" : "bg-slate-700 text-slate-300"}`}>{item.is_required ? "Required" : "Recommended"}</span></td></tr>)}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
