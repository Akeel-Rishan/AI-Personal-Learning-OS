"use client";

import { useCallback, useEffect, useReducer, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, apiPost, apiPut } from "@/lib/api";
import type { GoalDecomposition, GoalDraft, GoalSummary } from "@/lib/goals";
import { StepGoalInput } from "@/components/goal/StepGoalInput";
import { StepReview } from "@/components/goal/StepReview";
import { StepTimeSetup } from "@/components/goal/StepTimeSetup";

const STORAGE_KEY = "goal_wizard_progress_v1";

interface WizardState {
  step: 1 | 2 | 3;
  draft: GoalDraft;
  errors: Record<string, string>;
  goalId: string | null;
  decomposition: GoalDecomposition | null;
  decompositionStatus: "idle" | "loading" | "success" | "error";
  apiError: string | null;
}

type WizardAction =
  | { type: "HYDRATE"; state: Partial<WizardState> }
  | { type: "PATCH_DRAFT"; patch: Partial<GoalDraft> }
  | { type: "SET_ERRORS"; errors: Record<string, string> }
  | { type: "SET_STEP"; step: 1 | 2 | 3 }
  | { type: "DECOMPOSE_START" }
  | { type: "SET_GOAL_ID"; goalId: string }
  | { type: "DECOMPOSE_SUCCESS"; result: GoalDecomposition }
  | { type: "DECOMPOSE_ERROR"; message: string }
  | { type: "RETRY" };

const initialState: WizardState = {
  step: 1,
  draft: { title: "", targetRole: "", existingKnowledge: "", dailyMinutes: 60, targetDate: "" },
  errors: {},
  goalId: null,
  decomposition: null,
  decompositionStatus: "idle",
  apiError: null,
};

function reducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case "HYDRATE":
      return {
        ...state,
        ...action.state,
        draft: { ...state.draft, ...action.state.draft },
        errors: {},
        decompositionStatus: action.state.decomposition ? "success" : "idle",
        apiError: null,
      };
    case "PATCH_DRAFT":
      return { ...state, draft: { ...state.draft, ...action.patch }, errors: {} };
    case "SET_ERRORS":
      return { ...state, errors: action.errors };
    case "SET_STEP":
      return { ...state, step: action.step, errors: {} };
    case "DECOMPOSE_START":
      return { ...state, decompositionStatus: "loading", apiError: null };
    case "SET_GOAL_ID":
      return { ...state, goalId: action.goalId };
    case "DECOMPOSE_SUCCESS":
      return { ...state, decompositionStatus: "success", decomposition: action.result, apiError: null };
    case "DECOMPOSE_ERROR":
      return { ...state, decompositionStatus: "error", apiError: action.message };
    case "RETRY":
      return { ...state, decompositionStatus: "idle", apiError: null };
    default:
      return state;
  }
}

function validateStep(state: WizardState): Record<string, string> {
  const errors: Record<string, string> = {};
  if (state.step === 1) {
    if (state.draft.title.trim().length < 10) errors.title = "Describe your goal in at least 10 characters.";
    if (state.draft.title.length > 300) errors.title = "Keep your goal under 300 characters.";
  }
  if (state.step === 2 && state.draft.targetDate) {
    const minimum = new Date();
    minimum.setHours(0, 0, 0, 0);
    minimum.setDate(minimum.getDate() + 30);
    if (new Date(`${state.draft.targetDate}T00:00:00`) < minimum) errors.targetDate = "Choose a date at least 30 days from today.";
  }
  return errors;
}

function friendlyError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 503) return "OpenAI is not configured yet. Add your OpenAI API key to backend/.env, restart the backend, and retry.";
    if (error.status === 0) return "The learning service is unreachable. Check that the backend is running and try again.";
    return error.message;
  }
  return "We couldn't generate your roadmap. Please try again.";
}

const steps = ["Your Goal", "Time & Schedule", "Review Plan"];

export function GoalWizard(): JSX.Element {
  const router = useRouter();
  const [state, dispatch] = useReducer(reducer, initialState);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) dispatch({ type: "HYDRATE", state: JSON.parse(saved) as Partial<WizardState> });
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
    } finally {
      setHydrated(true);
    }
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [hydrated, state]);

  const buildPlan = useCallback(async (): Promise<void> => {
    dispatch({ type: "DECOMPOSE_START" });
    try {
      const payload = {
        title: state.draft.title.trim(),
        description: null,
        target_role: state.draft.targetRole.trim() || null,
        daily_study_minutes: state.draft.dailyMinutes,
        target_date: state.draft.targetDate || null,
        existing_knowledge: state.draft.existingKnowledge.trim(),
      };
      let goalId = state.goalId;
      if (!goalId) {
        const goal = await apiPost<GoalSummary>("/api/v1/goals/", payload);
        goalId = goal.id;
        dispatch({ type: "SET_GOAL_ID", goalId });
      } else {
        await apiPut<GoalSummary>(`/api/v1/goals/${goalId}`, payload);
      }
      const result = await apiPost<GoalDecomposition>(`/api/v1/goals/${goalId}/decompose`, {
        goal_id: goalId,
        existing_knowledge: state.draft.existingKnowledge.trim(),
      });
      dispatch({ type: "DECOMPOSE_SUCCESS", result });
    } catch (error: unknown) {
      dispatch({ type: "DECOMPOSE_ERROR", message: friendlyError(error) });
    }
  }, [state.draft, state.goalId]);

  useEffect(() => {
    if (hydrated && state.step === 3 && state.decompositionStatus === "idle") void buildPlan();
  }, [buildPlan, hydrated, state.decompositionStatus, state.step]);

  function next(): void {
    const errors = validateStep(state);
    if (Object.keys(errors).length > 0) {
      dispatch({ type: "SET_ERRORS", errors });
      return;
    }
    dispatch({ type: "SET_STEP", step: Math.min(3, state.step + 1) as 1 | 2 | 3 });
  }

  function back(): void {
    if (state.step > 1 && state.decompositionStatus !== "loading") dispatch({ type: "SET_STEP", step: (state.step - 1) as 1 | 2 });
  }

  function confirm(): void {
    window.localStorage.removeItem(STORAGE_KEY);
    router.push("/dashboard");
  }

  if (!hydrated) {
    return <div className="mx-auto flex min-h-[500px] max-w-4xl items-center justify-center"><span className="h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-sky-400" /></div>;
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/70 px-4 py-5 sm:px-8">
        <ol className="grid grid-cols-3">
          {steps.map((label, index) => {
            const number = index + 1;
            const completed = state.step > number;
            const current = state.step === number;
            return (
              <li key={label} className="relative flex flex-col items-center text-center">
                {index > 0 && <span className={`absolute right-1/2 top-4 h-0.5 w-full ${state.step > index ? "bg-emerald-400" : "bg-slate-700"}`} />}
                <span className={`relative z-10 flex h-8 w-8 items-center justify-center rounded-full border text-sm font-bold transition ${completed ? "border-emerald-400 bg-emerald-400 text-slate-950" : current ? "border-sky-400 bg-sky-400 text-slate-950" : "border-slate-600 bg-slate-900 text-slate-500"}`}>{completed ? "✓" : number}</span>
                <span className={`mt-2 text-[11px] sm:text-sm ${current ? "font-semibold text-sky-300" : completed ? "text-emerald-300" : "text-slate-500"}`}>{label}</span>
              </li>
            );
          })}
        </ol>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-2xl shadow-black/10 sm:p-9">
        {state.step === 1 && <StepGoalInput draft={state.draft} errors={state.errors} onChange={(patch) => dispatch({ type: "PATCH_DRAFT", patch })} />}
        {state.step === 2 && <StepTimeSetup draft={state.draft} errors={state.errors} onChange={(patch) => dispatch({ type: "PATCH_DRAFT", patch })} />}
        {state.step === 3 && <StepReview status={state.decompositionStatus} result={state.decomposition} error={state.apiError} onRetry={() => dispatch({ type: "RETRY" })} onConfirm={confirm} />}

        {state.step < 3 && (
          <div className="mt-9 flex items-center justify-between border-t border-slate-800 pt-6">
            <button type="button" disabled={state.step === 1} onClick={back} className="rounded-xl border border-slate-700 px-5 py-3 text-sm font-semibold text-slate-300 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-30">← Back</button>
            <button type="button" onClick={next} className="rounded-xl bg-sky-400 px-6 py-3 text-sm font-bold text-slate-950 transition hover:bg-sky-300">Next →</button>
          </div>
        )}
        {state.step === 3 && state.decompositionStatus !== "loading" && (
          <button type="button" onClick={back} className="mt-6 text-sm font-semibold text-slate-500 transition hover:text-slate-300">← Edit goal details</button>
        )}
      </div>
    </div>
  );
}
