export function OfflinePulse() {
  return (
    <div
      className="flex items-center gap-2 rounded-full border border-ink-600 bg-ink-800/60 px-3 py-1.5"
      title="DOCBOT runs entirely on local infrastructure -- no data leaves this machine"
    >
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-breathe rounded-full bg-sage-500" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-sage-500" />
      </span>
      <span className="font-mono text-[11px] uppercase tracking-wider text-paper-300">Local only</span>
    </div>
  );
}
