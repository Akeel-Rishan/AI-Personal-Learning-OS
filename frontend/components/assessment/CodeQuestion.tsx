"use client";

export function CodeQuestion({ code, value, onChange, disabled }: { code: string; value: string; onChange: (value: string) => void; disabled: boolean }): JSX.Element {
  return (
    <div className="space-y-4">
      {code && <pre className="overflow-x-auto rounded-xl border border-slate-700 bg-[#1e1e1e] p-4 text-sm leading-7 text-slate-200"><code>{code.split("\n").map((line, index) => <span key={index} className="table-row"><span className="table-cell select-none pr-5 text-right text-slate-600">{index + 1}</span><span className="table-cell whitespace-pre">{line}</span></span>)}</code></pre>}
      <textarea value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} rows={7} maxLength={12000} placeholder="Write your fix or answer here..." spellCheck={false} className="w-full rounded-xl border border-slate-700 bg-slate-950 p-4 font-mono text-sm leading-7 outline-none transition placeholder:text-slate-600 focus:border-sky-400" />
    </div>
  );
}
