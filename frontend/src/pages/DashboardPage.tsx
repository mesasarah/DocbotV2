import { useQuery } from "@tanstack/react-query";
import { FileText, Layers, CheckCircle2, Clock, Network, ScanText } from "lucide-react";
import { AreaChart, Area, ResponsiveContainer, XAxis, Tooltip, PieChart, Pie, Cell } from "recharts";
import { getAnalyticsSummary } from "../api/analytics";
import { useAuth } from "../hooks/useAuth";

function StatCard({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: typeof FileText;
  label: string;
  value: string | number;
  accent: string;
}) {
  return (
    <div className="rounded-xl border border-ink-700 bg-ink-800/40 p-5">
      <div className={`mb-3 flex h-9 w-9 items-center justify-center rounded-lg ${accent}`}>
        <Icon size={17} />
      </div>
      <p className="font-mono text-2xl font-semibold text-paper-100">{value}</p>
      <p className="text-sm text-paper-300">{label}</p>
    </div>
  );
}

const TYPE_PALETTE = ["#E8577E", "#7FA894", "#D9A441", "#93B9A2", "#9A9CA8"];

export function DashboardPage() {
  const { user } = useAuth();
  const { data } = useQuery({ queryKey: ["analytics"], queryFn: getAnalyticsSummary });

  const typeData = Object.entries(data?.documents_by_type ?? {}).map(([type, count], i) => ({
    name: type,
    value: count,
    color: TYPE_PALETTE[i % TYPE_PALETTE.length],
  }));

  return (
    <div className="mx-auto max-w-4xl px-8 py-8">
      <h1 className="text-lg font-semibold text-paper-100">Welcome back, {user?.full_name?.split(" ")[0]}</h1>
      <p className="mb-6 text-sm text-paper-300">Here's what's indexed and ready to query.</p>

      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
        <StatCard icon={FileText} label="Documents" value={data?.total_documents ?? 0} accent="bg-rose-500/15 text-rose-400" />
        <StatCard icon={CheckCircle2} label="Indexed" value={data?.indexed_documents ?? 0} accent="bg-sage-500/15 text-sage-400" />
        <StatCard icon={Clock} label="Processing" value={data?.processing_documents ?? 0} accent="bg-amber-500/15 text-amber-400" />
        <StatCard icon={Layers} label="Total chunks" value={data?.total_chunks ?? 0} accent="bg-paper-100/10 text-paper-200" />
        <StatCard icon={Network} label="Entities" value={data?.total_entities ?? 0} accent="bg-rose-500/15 text-rose-400" />
        <StatCard icon={ScanText} label="OCR pages" value={data?.total_ocr_pages ?? 0} accent="bg-amber-500/15 text-amber-400" />
      </div>

      {data && data.total_documents > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="md:col-span-2 rounded-xl border border-ink-700 bg-ink-800/40 p-5">
            <p className="mb-3 text-sm font-medium text-paper-100">Uploads, last 14 days</p>
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={data.uploads_by_day}>
                <defs>
                  <linearGradient id="uploadsGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#E8577E" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#E8577E" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#9A9CA8", fontSize: 10, fontFamily: "JetBrains Mono, monospace" }}
                  tickFormatter={(d: string) => d.slice(5)}
                  axisLine={{ stroke: "#343945" }}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "#1B1E25",
                    border: "1px solid #343945",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: "#EDEDEF" }}
                />
                <Area type="monotone" dataKey="count" stroke="#E8577E" strokeWidth={2} fill="url(#uploadsGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-xl border border-ink-700 bg-ink-800/40 p-5">
            <p className="mb-3 text-sm font-medium text-paper-100">By file type</p>
            {typeData.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={120}>
                  <PieChart>
                    <Pie data={typeData} dataKey="value" nameKey="name" innerRadius={30} outerRadius={50}>
                      {typeData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-2 flex flex-col gap-1">
                  {typeData.map((t) => (
                    <div key={t.name} className="flex items-center gap-1.5 font-mono text-[11px] text-paper-300">
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: t.color }} />
                      {t.name} · {t.value}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm text-paper-300">No documents yet</p>
            )}
          </div>
        </div>
      )}

      {(!data || data.total_documents === 0) && (
        <div className="mt-6 rounded-xl border border-ink-700 bg-ink-800/30 px-6 py-10 text-center">
          <p className="text-sm text-paper-200">Nothing indexed yet</p>
          <p className="text-sm text-paper-300">Head to Documents to upload your first file.</p>
        </div>
      )}
    </div>
  );
}
