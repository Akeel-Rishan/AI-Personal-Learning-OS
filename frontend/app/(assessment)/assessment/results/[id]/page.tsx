"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ResultsChart } from "@/components/assessment/ResultsChart";
import { ApiError, apiGet, apiPost } from "@/lib/api";
import type { AssessmentResults, SkillScore } from "@/lib/assessments";
import type { Roadmap } from "@/lib/roadmaps";

function skillStatus(skill: SkillScore): string {
  return skill.mastery_score >= 0.8 ? "Mastered" : skill.mastery_score >= 0.5 ? "Learning" : "Needs Work";
}

export default function ResultsPage(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [results, setResults] = useState<AssessmentResults | null>(null);
  const [details, setDetails] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [roadmapState, setRoadmapState] = useState<"idle" | "generating" | "ready" | "error">("idle");

  useEffect(() => {
    let active = true;
    apiGet<AssessmentResults>(`/api/v1/assessments/${id}/results`)
      .then((value) => { if (active) setResults(value); })
      .catch((reason: unknown) => {
        if (!active) return;
        if (reason instanceof ApiError && [401, 403, 404].includes(reason.status)) router.replace("/dashboard");
        else setError(reason instanceof ApiError && reason.status === 409 ? "Finish the assessment before viewing results." : "We couldn't load your results.");
      });
    return () => { active = false; };
  }, [id, router]);

  useEffect(() => {
    if (!results?.goal_id) return;
    let active = true;
    apiGet<Roadmap>(`/api/v1/roadmaps/goal/${results.goal_id}`)
      .then(() => { if (active) setRoadmapState("ready"); })
      .catch(async (reason: unknown) => {
        if (!active) return;
        if (!(reason instanceof ApiError && reason.status === 404)) { setRoadmapState("error"); return; }
        setRoadmapState("generating");
        try {
          await apiPost<Roadmap>("/api/v1/roadmaps/generate", { goal_id: results.goal_id });
          if (active) setRoadmapState("ready");
        } catch { if (active) setRoadmapState("error"); }
      });
    return () => { active = false; };
  }, [results]);

  if (error) return <main className="flex min-h-screen items-center justify-center bg-slate-950 p-4 text-slate-100"><div className="text-center"><h1 className="text-2xl font-bold">Results unavailable</h1><p className="mt-3 text-slate-400">{error}</p><Link href={`/assessment/${id}`} className="mt-6 inline-block text-sky-400">Return to assessment →</Link></div></main>;
  if (!results) return <main className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-400"><div className="text-center"><span className="mx-auto block h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-emerald-400" /><p className="mt-4">Building your skill profile...</p></div></main>;

  return <main className="min-h-screen bg-slate-950 px-4 py-12 text-slate-100 sm:px-6"><div className="mx-auto max-w-5xl">
    <section className="text-center"><div className="mx-auto flex h-40 w-40 items-center justify-center rounded-full bg-[conic-gradient(#38bdf8_var(--score),#1e293b_0)] p-3" style={{ "--score": `${results.overall_score * 3.6}deg` } as React.CSSProperties}><div className="flex h-full w-full items-center justify-center rounded-full bg-slate-950 text-4xl font-black">{Math.round(results.overall_score)}%</div></div><p className="mt-7 text-sm font-bold uppercase tracking-[0.25em] text-emerald-400">Assessment complete</p><h1 className="mt-2 text-3xl font-bold sm:text-4xl">Your starting point is mapped!</h1><p className="mt-3 text-slate-400">{results.correct_answers} of {results.total_questions} essentially correct{results.completed_at ? ` · ${new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(results.completed_at))}` : ""}</p></section>
    {roadmapState === "generating" && <div className="mt-8 rounded-xl border border-sky-400/20 bg-sky-400/5 p-4 text-center text-sm text-sky-200"><span className="mr-3 inline-block h-4 w-4 animate-spin rounded-full border-2 border-sky-900 border-t-sky-300 align-[-3px]" />Your personalized roadmap is being generated in the background...</div>}
    <section className="mt-12 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-8"><h2 className="text-2xl font-bold">Skills breakdown</h2><p className="mt-2 text-slate-400">This profile sets the pace and emphasis of your roadmap.</p><div className="mt-8"><ResultsChart skills={results.skill_scores} /></div></section>
    <section className="mt-6 grid gap-5 md:grid-cols-2"><div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/5 p-6"><h2 className="font-bold text-emerald-300">Strong Areas</h2><div className="mt-4 space-y-2">{results.strong_skills.length ? results.strong_skills.map((skill) => <p key={skill.skill_id} className="flex justify-between"><span>{skill.skill_name}</span><b>{Math.round(skill.mastery_percentage)}%</b></p>) : <p className="text-sm text-slate-400">These will emerge as you learn—everyone starts somewhere.</p>}</div></div><div className="rounded-2xl border border-red-400/20 bg-red-400/5 p-6"><h2 className="font-bold text-red-300">Areas to Improve</h2><div className="mt-4 space-y-2">{results.weak_skills.length ? results.weak_skills.map((skill) => <p key={skill.skill_id} className="flex justify-between"><span>{skill.skill_name}</span><b>{Math.round(skill.mastery_percentage)}%</b></p>) : <p className="text-sm text-slate-400">No major gaps detected in this assessment.</p>}</div></div></section>
    <section className="mt-6 rounded-2xl border border-sky-400/20 bg-sky-400/5 p-6 sm:p-8"><h2 className="text-xl font-bold">What happens next?</h2><p className="mt-3 max-w-3xl leading-7 text-slate-300">Based on your results, we&apos;ve personalized your learning roadmap. Strong skills are fast-tracked while gaps receive more attention.</p><div className="mt-6 flex flex-wrap gap-3">{roadmapState === "ready" ? <Link href="/roadmap" className="rounded-xl bg-sky-400 px-5 py-3 font-bold text-slate-950">View My Roadmap →</Link> : <button type="button" disabled className="rounded-xl bg-slate-800 px-5 py-3 font-bold text-slate-500">{roadmapState === "error" ? "Roadmap generation needs a retry" : "Generating your roadmap..."}</button>}<Link href="/dashboard" className="rounded-xl border border-slate-700 px-5 py-3 font-bold">Go to Dashboard</Link></div></section>
    <section className="mt-6 overflow-hidden rounded-2xl border border-slate-800"><button type="button" onClick={() => setDetails((value) => !value)} className="flex w-full justify-between bg-slate-900/70 p-5 text-left font-bold">Skill details <span>{details ? "−" : "+"}</span></button>{details && <div className="overflow-x-auto"><table className="w-full min-w-[650px] text-left text-sm"><thead className="text-slate-500"><tr><th className="p-4">Skill Name</th><th className="p-4">Category</th><th className="p-4">Score</th><th className="p-4">Questions</th><th className="p-4">Status</th></tr></thead><tbody className="divide-y divide-slate-800">{results.skill_scores.map((skill) => <tr key={skill.skill_id}><td className="p-4 font-semibold">{skill.skill_name}</td><td className="p-4 capitalize text-slate-400">{skill.category.replaceAll("-", " ")}</td><td className="p-4">{Math.round(skill.mastery_percentage)}%</td><td className="p-4">{skill.questions_count}</td><td className="p-4"><span className="rounded-full bg-slate-800 px-2 py-1 text-xs">{skillStatus(skill)}</span></td></tr>)}</tbody></table></div>}</section>
  </div></main>;
}
