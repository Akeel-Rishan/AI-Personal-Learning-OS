"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ProjectDetail } from "@/components/projects/ProjectDetail";
import { getEligibility, getProject, startProject } from "@/lib/projects";
import type { Project } from "@/lib/projects";

export default function ProjectDetailPage(): JSX.Element {
  const { projectId } = useParams<{ projectId: string }>(); const router = useRouter();
  const [project, setProject] = useState<Project | null>(null); const [eligibility, setEligibility] = useState<{ eligible: boolean; recommendation: string } | null>(null); const [starting, setStarting] = useState(false); const [error, setError] = useState("");
  const load = useCallback(async (): Promise<void> => { setError(""); try { const [value, check] = await Promise.all([getProject(projectId), getEligibility(projectId)]); setProject(value); setEligibility(check); } catch (reason) { setError(reason instanceof Error ? reason.message : "Project details could not be loaded."); } }, [projectId]);
  useEffect(() => { void load(); }, [load]);
  const start = async (): Promise<void> => { if (!project) return; setStarting(true); setError(""); try { const workspace = await startProject(project.id); router.push(`/projects/workspace/${workspace.id}`); } catch (reason) { setError(reason instanceof Error ? reason.message : "The project could not be started."); } finally { setStarting(false); } };
  if (error && !project) return <div role="alert" className="mx-auto max-w-3xl rounded-xl border border-red-400/30 bg-red-400/5 p-5 text-red-200">{error}<button type="button" onClick={() => void load()} className="ml-4 rounded-lg border px-3 py-1">Retry</button></div>;
  if (!project || !eligibility) return <p className="py-20 text-center text-slate-400">Loading project…</p>;
  return <><ProjectDetail project={project} eligible={eligibility.eligible} recommendation={eligibility.recommendation} onStart={() => void start()} starting={starting} />{error && <p role="alert" className="mx-auto mt-4 max-w-5xl rounded-lg bg-red-400/10 p-3 text-sm text-red-200">{error}</p>}</>;
}
