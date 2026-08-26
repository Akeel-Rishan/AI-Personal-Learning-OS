import type { GoalDraft } from "@/lib/goals";

interface StepTimeSetupProps {
  draft: GoalDraft;
  errors: Record<string, string>;
  onChange: (patch: Partial<GoalDraft>) => void;
}

function durationLabel(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  if (!hours) return `${remainder} minutes`;
  if (!remainder) return `${hours} ${hours === 1 ? "hour" : "hours"}`;
  return `${hours} ${hours === 1 ? "hour" : "hours"} ${remainder} minutes`;
}

function minimumDate(): string {
  const value = new Date();
  value.setDate(value.getDate() + 30);
  return value.toISOString().slice(0, 10);
}

export function StepTimeSetup({ draft, errors, onChange }: StepTimeSetupProps): JSX.Element {
  const weeklyHours = draft.dailyMinutes * 7 / 60;
  const estimatedWeeks = Math.ceil(200 / weeklyHours);
  const targetWeeks = draft.targetDate
    ? Math.max(0, (new Date(`${draft.targetDate}T00:00:00`).getTime() - Date.now()) / 604800000)
    : null;
  const feasibility = targetWeeks === null
    ? "neutral"
    : targetWeeks >= estimatedWeeks
      ? "achievable"
      : targetWeeks >= estimatedWeeks * 0.85
        ? "tight"
        : "unlikely";
  const feasibilityStyles = {
    neutral: "border-sky-400/20 bg-sky-400/5 text-sky-200",
    achievable: "border-emerald-400/25 bg-emerald-400/5 text-emerald-200",
    tight: "border-amber-400/25 bg-amber-400/5 text-amber-200",
    unlikely: "border-red-400/25 bg-red-400/5 text-red-200",
  };

  return (
    <section className="animate-[wizard-enter_.3s_ease-out]">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-400">Step 2</p>
      <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">How much time can you dedicate?</h1>
      <p className="mt-3 text-slate-400">Choose a pace you can sustain. Consistency matters more than intensity.</p>

      <div className="mt-9 rounded-2xl border border-slate-800 bg-slate-950/60 p-5 sm:p-7">
        <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
          <label htmlFor="daily-time" className="font-semibold">Daily study time</label>
          <p className="text-2xl font-bold text-sky-300">{durationLabel(draft.dailyMinutes)} <span className="text-sm font-normal text-slate-500">per day</span></p>
        </div>
        <input
          id="daily-time"
          type="range"
          min={15}
          max={240}
          step={15}
          value={draft.dailyMinutes}
          onChange={(event) => onChange({ dailyMinutes: Number(event.target.value) })}
          className="mt-7 h-2 w-full cursor-pointer accent-sky-400"
        />
        <div className="mt-2 flex justify-between text-xs text-slate-600"><span>15 min</span><span>4 hours</span></div>
        <p className="mt-4 text-sm text-slate-400">That&apos;s about <span className="font-semibold text-slate-200">{weeklyHours.toFixed(1)} hours per week</span>.</p>
        <div className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[[30, "30 min"], [60, "1 hour"], [120, "2 hours"], [180, "3 hours"]].map(([minutes, label]) => (
            <button key={minutes} type="button" onClick={() => onChange({ dailyMinutes: Number(minutes) })} className={`rounded-lg border px-3 py-2 text-sm transition ${draft.dailyMinutes === minutes ? "border-sky-400 bg-sky-400/10 text-sky-300" : "border-slate-700 text-slate-400 hover:bg-slate-800"}`}>{label}</button>
          ))}
        </div>
      </div>

      <div className="mt-6">
        <label htmlFor="target-date" className="text-sm font-semibold text-slate-200">When do you want to achieve this goal? <span className="font-normal text-slate-500">Optional</span></label>
        <input
          id="target-date"
          type="date"
          min={minimumDate()}
          value={draft.targetDate}
          onChange={(event) => onChange({ targetDate: event.target.value })}
          className="mt-2 block w-full rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 outline-none focus:border-sky-400 sm:max-w-xs"
        />
        <p className="mt-2 text-xs text-slate-500">Leave blank and we&apos;ll estimate based on your pace.</p>
        {errors.targetDate && <p className="mt-2 text-sm text-red-400">{errors.targetDate}</p>}
      </div>

      <div className={`mt-7 rounded-2xl border p-5 ${feasibilityStyles[feasibility]}`}>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] opacity-70">Estimated timeline</p>
        <p className="mt-2 text-lg font-semibold">At {draft.dailyMinutes} min/day, this goal will take approximately {estimatedWeeks} weeks.</p>
        {feasibility !== "neutral" && <p className="mt-2 text-sm opacity-80">Your target date looks {feasibility === "achievable" ? "achievable at this pace" : feasibility === "tight" ? "tight but possible with consistency" : "too soon for the current study pace"}.</p>}
      </div>
    </section>
  );
}
