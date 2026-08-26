"use client";

export function TextQuestion({ value, onChange, disabled }: { value: string; onChange: (value: string) => void; disabled: boolean }): JSX.Element {
  return (
    <div>
      <textarea value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} onInput={(event) => { const target = event.currentTarget; target.style.height = "auto"; target.style.height = `${target.scrollHeight}px`; }} rows={5} maxLength={12000} placeholder="Write your explanation here... Don't worry about being perfect, just explain it in your own words." className="min-h-40 w-full resize-none rounded-xl border border-slate-700 bg-slate-950 p-4 leading-7 outline-none transition placeholder:text-slate-600 focus:border-sky-400" />
      <div className="mt-2 flex justify-between gap-3 text-xs"><span className="text-slate-500">Tip: Explain it as if you&apos;re teaching someone else.</span><span className={value.trim().length >= 20 ? "text-emerald-400" : "text-slate-500"}>{value.trim().length}/20 min</span></div>
    </div>
  );
}
