"use client";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { getWorkspace, saveProjectWork, submitProjectStage } from "@/lib/projects";
import type { Completion, StageEvaluation, UserProject, UserProjectStage } from "@/lib/projects";
import { MentorChat } from "./MentorChat"; import { MilestoneTracker } from "./MilestoneTracker"; import { ProjectCompletionCard } from "./ProjectCompletionCard"; import { ProjectSubmission } from "./ProjectSubmission"; import { StageContent } from "./StageContent"; import { StageNavigator } from "./StageNavigator";

interface StoredWorkspace { currentStageId?: string; drafts?: Record<string, { code?: string; notes?: string }>; hintIndexes?: Record<string, number> }
function readStored(key: string): StoredWorkspace { try { return JSON.parse(sessionStorage.getItem(key) ?? "{}"); } catch { return {}; } }

export function ProjectWorkspace({ initial }: { initial: UserProject }): JSX.Element {
  const [workspace, setWorkspace] = useState(initial); const storageKey = `project_workspace_${initial.id}`;
  const initialStage = initial.stage_progress.find((stage) => ["active", "submitted"].includes(stage.status)) ?? initial.stage_progress.at(-1)!;
  const [selectedId, setSelectedId] = useState(() => readStored(storageKey).currentStageId ?? initialStage.stage_id); const [code, setCode] = useState(""); const [notes, setNotes] = useState(""); const draftRef = useRef({ code: "", notes: "" }); const advanceTimer = useRef<number | null>(null);
  const [evaluation, setEvaluation] = useState<StageEvaluation | null>(null); const [submitting, setSubmitting] = useState(false); const [actionError, setActionError] = useState(""); const [notice, setNotice] = useState(""); const [savedAt, setSavedAt] = useState(""); const [tab, setTab] = useState<"work" | "mentor" | "stages">("work"); const [mentorFocus, setMentorFocus] = useState(0); const [completion, setCompletion] = useState<Completion | null>(null);
  const selected = useMemo(() => workspace.stage_progress.find((stage) => stage.stage_id === selectedId && stage.status !== "locked") ?? workspace.stage_progress.find((stage) => ["active", "submitted"].includes(stage.status)) ?? workspace.stage_progress.at(-1)!, [workspace, selectedId]);
  const mentorStage = useMemo(() => workspace.stage_progress.find((stage) => ["active", "submitted"].includes(stage.status)) ?? selected, [workspace, selected]);

  useEffect(() => () => { if (advanceTimer.current !== null) window.clearTimeout(advanceTimer.current); }, []);
  useEffect(() => {
    const server = workspace.work_data[`stage_${selected.stage_id}`] ?? {}; const stored = readStored(storageKey); const local = stored.drafts?.[selected.stage_id] ?? {};
    const next = { code: local.code ?? server.code ?? selected.submitted_code ?? "", notes: local.notes ?? server.notes ?? selected.submitted_notes ?? "" };
    setCode(next.code); setNotes(next.notes); draftRef.current = next; setEvaluation(selected.ai_feedback); setActionError("");
  }, [selected.stage_id, selected.submitted_code, selected.submitted_notes, selected.ai_feedback, storageKey, workspace.work_data]);
  useEffect(() => { draftRef.current = { code, notes }; const stored = readStored(storageKey); sessionStorage.setItem(storageKey, JSON.stringify({ ...stored, currentStageId: selected.stage_id, drafts: { ...(stored.drafts ?? {}), [selected.stage_id]: { code, notes } } })); }, [code, notes, selected.stage_id, storageKey]);
  useEffect(() => {
    if (selected.status === "completed") return;
    const timer = window.setInterval(() => { const draft = draftRef.current; void saveProjectWork(workspace.id, selected.stage_id, draft.code, draft.notes).then((result) => setSavedAt(result.saved_at)).catch((reason) => setActionError(reason instanceof Error ? reason.message : "Autosave failed.")); }, 30_000);
    return () => window.clearInterval(timer);
  }, [selected.stage_id, selected.status, workspace.id]);

  const choose = (stage: UserProjectStage): void => { setSelectedId(stage.stage_id); const stored = readStored(storageKey); sessionStorage.setItem(storageKey, JSON.stringify({ ...stored, currentStageId: stage.stage_id })); setTab("work"); setNotice(""); };
  const continueToActive = (): void => { const next = workspace.stage_progress.find((stage) => ["active", "submitted"].includes(stage.status)); if (next) choose(next); };
  const askMentor = (): void => { setTab("mentor"); setMentorFocus((value) => value + 1); window.setTimeout(() => document.getElementById("project-mentor-panel")?.scrollIntoView({ behavior: "smooth", block: "start" }), 0); };
  const submit = async (): Promise<void> => {
    setSubmitting(true); setActionError("");
    try {
      const result = await submitProjectStage(workspace.id, selected.stage_id, code, notes); setEvaluation(result);
      const fresh = await getWorkspace(workspace.id); setWorkspace(fresh);
      if (result.passed && !result.project_completed) { const next = fresh.stage_progress.find((stage) => ["active", "submitted"].includes(stage.status)); if (next) { advanceTimer.current = window.setTimeout(() => choose(next), 3_000); } }
    } catch (reason) { setActionError(reason instanceof Error ? reason.message : "The stage could not be submitted."); }
    finally { setSubmitting(false); }
  };

  const allDone = workspace.stage_progress.every((stage) => stage.status === "completed");
  if (completion) return <ProjectCompletionCard completion={completion} />;
  return <div className="mx-auto max-w-[1500px]"><header className="mb-5 flex flex-wrap items-center justify-between gap-3"><div><Link href="/projects" className="text-sm text-sky-300">← Back to Projects</Link><p className="mt-3 text-xs font-bold uppercase tracking-widest text-indigo-300">Project workspace</p><h1 className="text-2xl font-black">{workspace.project.title}</h1></div><div className="text-right"><b className="text-sky-300">{workspace.progress_percentage}%</b><p className="text-xs text-slate-500">{workspace.xp_earned} XP earned{savedAt ? ` · Saved ${new Date(savedAt).toLocaleTimeString()}` : ""}</p></div></header><MilestoneTracker stages={workspace.stage_progress} />{notice && <div role="status" className="mt-4 flex justify-between rounded-lg border border-amber-400/20 bg-amber-400/5 p-3 text-sm text-amber-200"><span>{notice}</span><button type="button" onClick={() => setNotice("")}>×</button></div>}<div className="mt-4 flex gap-2 lg:hidden">{([['work','Instructions'],['mentor','Mentor'],['stages','Stages']] as const).map(([value, label]) => <button type="button" key={value} onClick={() => setTab(value)} className={`flex-1 rounded-lg p-2 text-sm ${tab === value ? "bg-sky-400 font-bold text-slate-950" : "bg-slate-800"}`}>{label}</button>)}</div><div className="mt-5 grid gap-5 lg:grid-cols-[230px_minmax(0,1fr)_340px]"><aside className={`${tab === "stages" ? "block" : "hidden"} lg:block`}><StageNavigator stages={workspace.stage_progress} selectedId={selected.stage_id} onSelect={choose} onLocked={(stage) => setNotice(`${stage.stage.title} is locked. Complete the current stage first.`)} /></aside><main className={`${tab === "work" ? "block" : "hidden"} lg:block`}>{allDone ? <ProjectSubmission userProjectId={workspace.id} onComplete={setCompletion} /> : <StageContent progress={selected} userProjectId={workspace.id} code={code} notes={notes} onCode={setCode} onNotes={setNotes} onSubmit={() => void submit()} submitting={submitting} evaluation={evaluation} actionError={actionError} onAskMentor={askMentor} onContinue={continueToActive} />}</main><aside id="project-mentor-panel" className={`${tab === "mentor" ? "block" : "hidden"} scroll-mt-24 lg:block`}><MentorChat userProjectId={workspace.id} stageId={mentorStage.stage_id} focusToken={mentorFocus} /></aside></div></div>;
}
