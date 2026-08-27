import type { GapSeverity } from "@/lib/adaptive";

const styles: Record<GapSeverity, string> = {
  critical: "border-red-400/30 bg-red-400/10 text-red-300",
  high: "border-orange-400/30 bg-orange-400/10 text-orange-300",
  medium: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  low: "border-sky-400/30 bg-sky-400/10 text-sky-300",
};

export function GapSeverityBadge({ severity }: { severity: GapSeverity }): JSX.Element {
  return <span className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider ${styles[severity]}`}>{severity}</span>;
}
