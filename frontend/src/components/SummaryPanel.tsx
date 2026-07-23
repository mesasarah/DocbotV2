import type { SummaryResponse } from "../types/api";
import { Sparkles, ListChecks, Lightbulb } from "lucide-react";

export function SummaryPanel({ summary }: { summary: SummaryResponse }) {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-paper-300">
          <Sparkles size={13} />
          Executive summary
        </div>
        <p className="text-sm leading-relaxed text-paper-100">{summary.executive_summary}</p>
      </div>

      {summary.bullet_points.length > 0 && (
        <div>
          <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-paper-300">
            <ListChecks size={13} />
            Key points
          </div>
          <ul className="flex flex-col gap-1.5">
            {summary.bullet_points.map((point, i) => (
              <li key={i} className="flex gap-2 text-sm text-paper-100">
                <span className="text-rose-400">•</span>
                {point}
              </li>
            ))}
          </ul>
        </div>
      )}

      {summary.key_insights.length > 0 && (
        <div>
          <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-paper-300">
            <Lightbulb size={13} />
            Insights
          </div>
          <ul className="flex flex-col gap-1.5">
            {summary.key_insights.map((insight, i) => (
              <li key={i} className="rounded-lg bg-sage-500/10 px-3 py-2 text-sm text-sage-400">
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
