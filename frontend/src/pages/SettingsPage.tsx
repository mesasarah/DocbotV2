import { useQuery } from "@tanstack/react-query";
import { Cpu } from "lucide-react";
import { apiClient } from "../api/client";

interface ModelsResponse {
  current_model: string;
  available_models: string[];
}

export function SettingsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["llm-models"],
    queryFn: async () => (await apiClient.get<ModelsResponse>("/api/v1/settings/models")).data,
  });

  return (
    <div className="mx-auto max-w-2xl px-8 py-8">
      <h1 className="text-lg font-semibold text-paper-100">Settings</h1>
      <p className="mb-6 text-sm text-paper-300">DOCBOT runs entirely on local infrastructure.</p>

      <div className="rounded-xl border border-ink-700 bg-ink-800/40 p-5">
        <div className="mb-3 flex items-center gap-2">
          <Cpu size={16} className="text-rose-400" />
          <h2 className="text-sm font-medium text-paper-100">Local LLM (Ollama)</h2>
        </div>

        {isLoading ? (
          <p className="text-sm text-paper-300">Checking Ollama…</p>
        ) : (
          <>
            <p className="text-sm text-paper-300">
              Active model: <span className="font-mono text-paper-100">{data?.current_model}</span>
            </p>
            <p className="mt-1 text-sm text-paper-300">
              Available models on this machine:{" "}
              {data?.available_models.length ? (
                <span className="font-mono text-paper-100">{data.available_models.join(", ")}</span>
              ) : (
                <span className="text-amber-400">
                  none found — run <span className="font-mono">ollama pull llama3</span>
                </span>
              )}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
