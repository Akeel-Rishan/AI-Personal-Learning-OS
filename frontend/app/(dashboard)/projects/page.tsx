"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { ProjectLibrary } from "@/components/projects/ProjectLibrary";
import { getMyProjects, getProjects, getRecommendedProjects, startProject } from "@/lib/projects";
import type { ProjectLibraryItem } from "@/lib/projects";

export default function ProjectsPage(): JSX.Element {
  const router = useRouter();
  const [items, setItems] = useState<ProjectLibraryItem[]>([]);
  const [recommended, setRecommended] = useState<ProjectLibraryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState<string | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async (): Promise<void> => {
    setLoading(true); setError("");
    try {
      const [all, rec] = await Promise.all([getProjects(), getRecommendedProjects(), getMyProjects()]);
      setItems(all); setRecommended(rec);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Projects could not be loaded.");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);
  const start = async (id: string): Promise<void> => {
    setStarting(id); setError("");
    try { const workspace = await startProject(id); router.push(`/projects/workspace/${workspace.id}`); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "The project could not be started."); }
    finally { setStarting(null); }
  };

  if (loading) return <p className="py-20 text-center text-slate-400">Loading project library…</p>;
  const active = items.filter((item) => item.user_status === "active");
  return <div className="mx-auto max-w-7xl"><header><p className="text-xs font-bold uppercase tracking-widest text-indigo-300">Project-based learning</p><h1 className="mt-2 text-4xl font-black">Build something real</h1><p className="mt-3 max-w-2xl text-slate-400">Apply your skills through guided, portfolio-ready projects with an AI mentor beside you.</p></header>{error && <div role="alert" className="mt-6 flex items-center justify-between gap-4 rounded-xl border border-red-400/30 bg-red-400/5 p-4 text-sm text-red-200"><span>{error}</span><button type="button" onClick={() => void load()} className="rounded-lg border border-red-300/30 px-3 py-1.5 font-bold">Retry</button></div>}{active.length > 0 && <section className="mt-9"><h2 className="text-xl font-bold">My Active Projects</h2><div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{active.slice(0, 3).map((project) => <ProjectCard key={project.id} project={project} />)}</div></section>}{recommended.length > 0 && <section className="mt-9"><h2 className="text-xl font-bold">Recommended for You</h2><div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{recommended.slice(0, 3).map((project) => <ProjectCard key={project.id} project={project} onStart={(id) => void start(id)} starting={starting === project.id} />)}</div></section>}<section className="mt-10"><h2 className="mb-4 text-xl font-bold">Project Library</h2><ProjectLibrary projects={items} onStart={(id) => void start(id)} startingId={starting} /></section></div>;
}
