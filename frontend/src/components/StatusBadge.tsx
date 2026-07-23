import type { DocumentStatus } from "../types/api";

const config: Record<DocumentStatus, { label: string; classes: string; pulse?: boolean }> = {
  pending: { label: "Queued", classes: "bg-ink-600 text-paper-200" },
  processing: { label: "Processing", classes: "bg-amber-500/15 text-amber-400", pulse: true },
  indexed: { label: "Indexed", classes: "bg-sage-500/15 text-sage-400" },
  failed: { label: "Failed", classes: "bg-crimson-500/15 text-crimson-400" },
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const c = config[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-mono text-[11px] font-medium ${c.classes}`}
    >
      {c.pulse && <span className="h-1.5 w-1.5 rounded-full bg-current animate-breathe" />}
      {c.label}
    </span>
  );
}
