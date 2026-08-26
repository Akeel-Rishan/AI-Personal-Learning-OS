export function ProgressBar({ completed, total }: { completed: number; total: number }): JSX.Element {
  const percentage = total ? Math.min(100, Math.round((completed / total) * 100)) : 0;
  return (
    <div className="flex items-center gap-3" aria-label={`${percentage}% complete`}>
      <div className="flex h-2 flex-1 overflow-hidden rounded-full bg-slate-800">
        {Array.from({ length: total }, (_, index) => (
          <span key={index} className={`min-w-0 flex-1 border-r border-slate-950/40 transition-colors duration-500 ${index < completed ? "bg-emerald-400" : index === completed ? "animate-pulse bg-sky-400" : "bg-slate-700"}`} />
        ))}
      </div>
      <span className="w-10 text-right text-xs font-semibold text-slate-400">{percentage}%</span>
    </div>
  );
}
