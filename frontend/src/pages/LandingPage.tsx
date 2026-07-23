import { Link } from "react-router-dom";
import { MessageSquare, Network, ScanText, ShieldCheck, Sparkles, ArrowRight } from "lucide-react";

const features = [
  {
    icon: MessageSquare,
    title: "Ask, don't search",
    body: "Upload your documents and ask questions in plain language. Answers are grounded only in what you uploaded — cited, page by page.",
  },
  {
    icon: ScanText,
    title: "Reads scanned pages too",
    body: "PDFs that are just images of text get read automatically via on-device OCR — no manual step required.",
  },
  {
    icon: Network,
    title: "See how it connects",
    body: "An interactive knowledge graph surfaces the people, organizations, and relationships hiding across your documents.",
  },
  {
    icon: Sparkles,
    title: "Summaries & quizzes",
    body: "Turn a long document into an executive summary, key insights, or a quiz to test what you've learned.",
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-ink-950 text-paper-100">
      {/* ambient glow */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-rose-500/20 blur-[120px]" />
        <div className="absolute top-1/3 -right-40 h-[400px] w-[500px] rounded-full bg-rose-600/10 blur-[100px]" />
      </div>

      <div className="relative">
        {/* Nav */}
        <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-rose-400 to-rose-600 font-mono text-base font-bold text-ink-950 shadow-lg shadow-rose-500/20">
              D
            </div>
            <span className="text-sm font-semibold tracking-wide">DOCBOT 2.0</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm text-paper-200 hover:text-paper-100">
              Sign in
            </Link>
            <Link
              to="/register"
              className="rounded-lg bg-rose-500 px-4 py-2 text-sm font-semibold text-ink-950 transition-colors hover:bg-rose-400"
            >
              Create account
            </Link>
          </div>
        </header>

        {/* Hero */}
        <section className="mx-auto max-w-4xl px-6 pb-20 pt-16 text-center sm:pt-24">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-ink-600 bg-ink-800/60 px-3.5 py-1.5">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-breathe rounded-full bg-sage-500" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-sage-500" />
            </span>
            <span className="font-mono text-[11px] uppercase tracking-wider text-paper-300">
              Offline · Private · Local-first
            </span>
          </div>

          <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-6xl">
            Your documents,
            <br />
            <span className="bg-gradient-to-r from-rose-400 via-rose-500 to-rose-600 bg-clip-text text-transparent">
              finally answering back.
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-base text-paper-300 sm:text-lg">
            DOCBOT reads, understands, and answers questions about your documents — entirely on your own
            machine. No cloud APIs, no data leaving your network, no compromise on privacy.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              to="/documents"
              className="group flex items-center gap-2 rounded-lg bg-rose-500 px-6 py-3 text-sm font-semibold text-ink-950 shadow-lg shadow-rose-500/25 transition-all hover:bg-rose-400 hover:shadow-rose-500/40"
            >
              Get started
              <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              to="/login"
              className="rounded-lg border border-ink-600 px-6 py-3 text-sm font-medium text-paper-200 transition-colors hover:border-ink-500 hover:text-paper-100"
            >
              I already have an account
            </Link>
          </div>
        </section>

        {/* Feature grid */}
        <section className="mx-auto max-w-5xl px-6 pb-24">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {features.map(({ icon: Icon, title, body }) => (
              <div
                key={title}
                className="group rounded-xl border border-ink-700 bg-ink-800/40 p-6 transition-colors hover:border-rose-500/30 hover:bg-ink-800/70"
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-rose-500/10 text-rose-400 transition-colors group-hover:bg-rose-500/20">
                  <Icon size={18} />
                </div>
                <h3 className="mb-1.5 text-sm font-semibold text-paper-100">{title}</h3>
                <p className="text-sm leading-relaxed text-paper-300">{body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Trust strip */}
        <section className="mx-auto max-w-4xl px-6 pb-24">
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-ink-700 bg-gradient-to-b from-ink-800/60 to-ink-800/20 px-8 py-10 text-center">
            <ShieldCheck size={22} className="text-sage-400" />
            <p className="max-w-md text-sm text-paper-200">
              Every document you upload, every question you ask, and every answer DOCBOT gives stays on the
              machine it runs on. There is no server to breach, because there is no server — just yours.
            </p>
          </div>
        </section>

        <footer className="mx-auto max-w-6xl px-6 pb-10 text-center">
          <p className="text-xs text-paper-300">DOCBOT 2.0 — offline document intelligence.</p>
        </footer>
      </div>
    </div>
  );
}
