import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Network, Sparkles } from "lucide-react";
import { getKnowledgeGraph, extractEntities } from "../api/knowledgeGraph";
import { listDocuments } from "../api/documents";
import { extractErrorMessage } from "../api/client";
import type { EntityType, GraphNode } from "../types/api";

const TYPE_COLORS: Record<EntityType, string> = {
  PERSON: "#E8577E",
  ORGANIZATION: "#7FA894",
  LOCATION: "#D9A441",
  TECHNOLOGY: "#93B9A2",
  DATE: "#9A9CA8",
  OTHER: "#4A505E",
};

interface PositionedNode extends GraphNode {
  x: number;
  y: number;
}

// Simple radial layout grouped by entity type -- not a physics simulation,
// but organized and legible, which matters more for a demo graph than
// true force-directed placement would.
function layoutNodes(nodes: GraphNode[], width: number, height: number): PositionedNode[] {
  const cx = width / 2;
  const cy = height / 2;
  const byType = new Map<string, GraphNode[]>();
  for (const n of nodes) {
    if (!byType.has(n.type)) byType.set(n.type, []);
    byType.get(n.type)!.push(n);
  }

  const positioned: PositionedNode[] = [];
  const types = Array.from(byType.keys());
  types.forEach((type, typeIdx) => {
    const typeAngleStart = (typeIdx / types.length) * 2 * Math.PI;
    const typeAngleSpan = (2 * Math.PI) / types.length;
    const group = byType.get(type)!;
    group.forEach((node, i) => {
      const angle = typeAngleStart + (typeAngleSpan * (i + 0.5)) / group.length;
      const radius = Math.min(width, height) * 0.36;
      positioned.push({
        ...node,
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      });
    });
  });
  return positioned;
}

export function KnowledgeGraphPage() {
  const queryClient = useQueryClient();
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [extractError, setExtractError] = useState<string | null>(null);

  const { data: documents } = useQuery({ queryKey: ["documents"], queryFn: listDocuments });
  const indexedDocs = (documents?.documents ?? []).filter((d) => d.status === "indexed");

  const { data: graph, isLoading } = useQuery({
    queryKey: ["knowledge-graph"],
    queryFn: () => getKnowledgeGraph(),
  });

  const extractMutation = useMutation({
    mutationFn: extractEntities,
    onSuccess: () => {
      setExtractError(null);
      queryClient.invalidateQueries({ queryKey: ["knowledge-graph"] });
    },
    onError: (err) => setExtractError(extractErrorMessage(err, "Couldn't extract entities.")),
  });

  const width = 760;
  const height = 480;
  const positionedNodes = useMemo(
    () => layoutNodes(graph?.nodes ?? [], width, height),
    [graph?.nodes]
  );
  const nodeById = useMemo(() => new Map(positionedNodes.map((n) => [n.id, n])), [positionedNodes]);

  const visibleTypes = useMemo(() => {
    const types = new Set<string>();
    (graph?.nodes ?? []).forEach((n) => types.add(n.type));
    return Array.from(types) as EntityType[];
  }, [graph?.nodes]);

  return (
    <div className="mx-auto max-w-5xl px-8 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-paper-100">Knowledge Graph</h1>
          <p className="text-sm text-paper-300">
            Entities and relationships extracted across your documents by the local LLM.
          </p>
          <p className="mt-1 text-xs text-paper-300/70">
            Extraction runs per document, on demand — pick a document and click "Extract entities" to
            add it to the graph. It won't happen automatically on upload, since each run is a full LLM
            call.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="rounded-lg border border-ink-600 bg-ink-800 px-3 py-2 text-sm text-paper-100 outline-none focus:border-rose-500"
          >
            <option value="">Select a document…</option>
            {indexedDocs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.original_filename}
              </option>
            ))}
          </select>
          <button
            onClick={() => selectedDocId && extractMutation.mutate(selectedDocId)}
            disabled={!selectedDocId || extractMutation.isPending}
            className="flex items-center gap-2 rounded-lg bg-rose-500 px-3.5 py-2 text-sm font-semibold text-ink-950 hover:bg-rose-400 disabled:opacity-40"
          >
            <Sparkles size={14} />
            {extractMutation.isPending ? "Extracting…" : "Extract entities"}
          </button>
        </div>
      </div>

      {extractError && (
        <div className="mb-4 rounded-lg bg-crimson-500/10 px-3.5 py-2.5 text-sm text-crimson-400">{extractError}</div>
      )}

      {isLoading ? (
        <p className="text-sm text-paper-300">Loading graph…</p>
      ) : !graph || graph.nodes.length === 0 ? (
        <div className="rounded-xl border border-ink-700 bg-ink-800/30 px-6 py-16 text-center">
          <Network size={24} className="mx-auto mb-3 text-paper-300" />
          <p className="text-sm text-paper-200">No entities extracted yet</p>
          <p className="text-sm text-paper-300">
            Pick a document above and click "Extract entities" to build the graph.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-ink-700 bg-ink-800/20 p-4">
          <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: 520 }}>
            {graph.edges.map((edge) => {
              const source = nodeById.get(edge.source);
              const target = nodeById.get(edge.target);
              if (!source || !target) return null;
              const isDimmed = hoveredNode && hoveredNode !== edge.source && hoveredNode !== edge.target;
              return (
                <g key={edge.id} opacity={isDimmed ? 0.15 : 0.5}>
                  <line
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke="#4A505E"
                    strokeWidth={1.5}
                  />
                  <text
                    x={(source.x + target.x) / 2}
                    y={(source.y + target.y) / 2}
                    fill="#9A9CA8"
                    fontSize={9}
                    fontFamily="JetBrains Mono, monospace"
                    textAnchor="middle"
                  >
                    {edge.label}
                  </text>
                </g>
              );
            })}

            {positionedNodes.map((node) => {
              const isDimmed = hoveredNode && hoveredNode !== node.id;
              const radius = 8 + Math.min(node.document_count, 5) * 1.5;
              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  opacity={isDimmed ? 0.3 : 1}
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  style={{ cursor: "pointer" }}
                >
                  <circle r={radius} fill={TYPE_COLORS[node.type]} fillOpacity={0.25} stroke={TYPE_COLORS[node.type]} strokeWidth={1.5} />
                  <circle r={2.5} fill={TYPE_COLORS[node.type]} />
                  <text
                    y={radius + 12}
                    fill="#EDEDEF"
                    fontSize={11}
                    fontFamily="Inter, sans-serif"
                    textAnchor="middle"
                  >
                    {node.name}
                  </text>
                </g>
              );
            })}
          </svg>

          <div className="mt-4 flex flex-wrap gap-3 border-t border-ink-700 pt-3">
            {visibleTypes.map((type) => (
              <div key={type} className="flex items-center gap-1.5 font-mono text-[11px] text-paper-300">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: TYPE_COLORS[type] }} />
                {type}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
