import type { GoalDraft } from "@/lib/goals";

interface StepGoalInputProps {
  draft: GoalDraft;
  errors: Record<string, string>;
  onChange: (patch: Partial<GoalDraft>) => void;
}

const popularGoals = [
  "Become an ML Engineer",
  "Learn Data Science",
  "Master Python",
  "Learn Deep Learning",
  "Become an AI Engineer",
  "Learn MLOps",
];

export function StepGoalInput({ draft, errors, onChange }: StepGoalInputProps): JSX.Element {
  return (
    <section className="animate-[wizard-enter_.3s_ease-out]">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-400">Step 1</p>
      <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">What do you want to achieve?</h1>
      <p className="mt-3 max-w-2xl text-slate-400">Be specific — the more detail you give, the better we can personalize your path.</p>

      <div className="mt-8 space-y-6">
        <div>
          <div className="flex items-end justify-between gap-4">
            <label htmlFor="goal-title" className="text-sm font-semibold text-slate-200">Goal title</label>
            <span className={`text-xs ${draft.title.length > 300 ? "text-red-400" : "text-slate-500"}`}>{draft.title.length}/300</span>
          </div>
          <textarea
            id="goal-title"
            rows={3}
            maxLength={300}
            value={draft.title}
            onChange={(event) => onChange({ title: event.target.value })}
            placeholder="e.g. I want to become a Machine Learning Engineer and build production AI systems"
            className="mt-2 w-full resize-none rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-lg outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-400/10"
            aria-describedby={errors.title ? "goal-title-error" : undefined}
          />
          {errors.title && <p id="goal-title-error" className="mt-2 text-sm text-red-400">{errors.title}</p>}
        </div>

        <div>
          <label htmlFor="target-role" className="text-sm font-semibold text-slate-200">What&apos;s your target role? <span className="font-normal text-slate-500">Optional</span></label>
          <input
            id="target-role"
            value={draft.targetRole}
            onChange={(event) => onChange({ targetRole: event.target.value })}
            placeholder="e.g. Machine Learning Engineer, Data Scientist, AI Engineer"
            className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-400/10"
          />
        </div>

        <div>
          <label htmlFor="existing-knowledge" className="text-sm font-semibold text-slate-200">What do you already know?</label>
          <textarea
            id="existing-knowledge"
            rows={4}
            value={draft.existingKnowledge}
            onChange={(event) => onChange({ existingKnowledge: event.target.value })}
            placeholder="e.g. I know basic Python and have done some web development. I'm comfortable with algebra but haven't studied statistics."
            className="mt-2 w-full resize-none rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-400/10"
          />
          <p className="mt-2 text-xs text-slate-500">This helps us skip what you already know and focus on gaps.</p>
        </div>

        <div>
          <p className="text-sm font-semibold text-slate-200">Or start with a popular goal</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {popularGoals.map((goal) => (
              <button
                key={goal}
                type="button"
                onClick={() => onChange({ title: goal })}
                className={`rounded-full border px-4 py-2 text-sm transition ${draft.title === goal ? "border-sky-400 bg-sky-400/10 text-sky-300" : "border-slate-700 text-slate-300 hover:border-slate-500 hover:bg-slate-800"}`}
              >
                {goal}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
