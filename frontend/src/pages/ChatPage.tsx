import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Send, Plus, MessageSquare, Trash2, FileText } from "lucide-react";
import { deleteChatSession, getChatHistory, listChatSessions, sendChatQuery } from "../api/chat";
import { extractErrorMessage } from "../api/client";
import type { ChatMessageRecord, SourceSnippet } from "../types/api";

interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceSnippet[];
}

export function ChatPage() {
  const queryClient = useQueryClient();
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: sessions } = useQuery({ queryKey: ["chat-sessions"], queryFn: listChatSessions });

  const historyQuery = useQuery({
    queryKey: ["chat-history", activeSessionId],
    queryFn: () => getChatHistory(activeSessionId!),
    enabled: !!activeSessionId,
  });

  useEffect(() => {
    if (historyQuery.data) {
      setMessages(
        historyQuery.data.messages.map((m: ChatMessageRecord) => ({
          id: m.id,
          role: m.role,
          content: m.content,
        }))
      );
    }
  }, [historyQuery.data]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const queryMutation = useMutation({
    mutationFn: (message: string) => sendChatQuery(message, activeSessionId ?? undefined),
    onSuccess: (res, message) => {
      setMessages((prev) => [
        ...prev,
        { id: `local-${Date.now()}-u`, role: "user", content: message },
        { id: `local-${Date.now()}-a`, role: "assistant", content: res.answer, sources: res.sources },
      ]);
      if (!activeSessionId) setActiveSessionId(res.session_id);
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
    onError: (err) => setErrorMsg(extractErrorMessage(err, "Couldn't get an answer. Try again.")),
  });

  const deleteSessionMutation = useMutation({
    mutationFn: deleteChatSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      setActiveSessionId(null);
      setMessages([]);
    },
  });

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || queryMutation.isPending) return;
    setErrorMsg(null);
    setInput("");
    queryMutation.mutate(trimmed);
  };

  const startNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setErrorMsg(null);
  };

  return (
    <div className="flex h-full">
      <aside className="flex w-64 flex-shrink-0 flex-col border-r border-ink-700 bg-ink-950/30">
        <div className="p-3">
          <button
            onClick={startNewChat}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-ink-600 bg-ink-800 px-3 py-2 text-sm text-paper-100 hover:bg-ink-700"
          >
            <Plus size={15} />
            New chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2">
          {sessions?.map((s) => (
            <div
              key={s.id}
              className={`group mb-1 flex items-center gap-2 rounded-lg px-3 py-2 text-sm cursor-pointer ${
                activeSessionId === s.id ? "bg-rose-500/10 text-rose-400" : "text-paper-200 hover:bg-ink-800"
              }`}
              onClick={() => setActiveSessionId(s.id)}
            >
              <MessageSquare size={14} className="flex-shrink-0" />
              <span className="truncate flex-1">{s.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteSessionMutation.mutate(s.id);
                }}
                className="hidden group-hover:block text-paper-300 hover:text-crimson-400"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-8 py-6">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <MessageSquare size={28} className="mb-3 text-paper-300" />
              <p className="text-sm text-paper-200">Ask anything about your documents</p>
              <p className="text-sm text-paper-300">Answers are grounded only in what you've uploaded.</p>
            </div>
          ) : (
            <div className="mx-auto flex max-w-2xl flex-col gap-5">
              {messages.map((m) => (
                <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[85%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                      m.role === "user" ? "bg-rose-500 text-ink-950 font-medium" : "bg-ink-800 text-paper-100"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{m.content}</p>
                    {m.sources && m.sources.length > 0 && (
                      <div className="mt-3 flex flex-col gap-1.5 border-t border-ink-600 pt-3">
                        {m.sources.map((s, i) => (
                          <div key={i} className="flex items-start gap-2 rounded-md bg-ink-900/60 px-2.5 py-1.5">
                            <FileText size={12} className="mt-0.5 flex-shrink-0 text-paper-300" />
                            <div className="min-w-0">
                              <p className="truncate font-mono text-[11px] text-paper-200">
                                {s.filename}
                                {s.page && ` · p.${s.page}`}
                                <span className="text-sage-400"> · {Math.round(s.score * 100)}% match</span>
                              </p>
                              <p className="truncate text-[11px] text-paper-300">{s.snippet}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {queryMutation.isPending && (
                <div className="flex justify-start">
                  <div className="rounded-xl bg-ink-800 px-4 py-3 text-sm text-paper-300">
                    <span className="inline-flex gap-1">
                      <span className="h-1.5 w-1.5 animate-breathe rounded-full bg-paper-300" />
                      <span className="h-1.5 w-1.5 animate-breathe rounded-full bg-paper-300 [animation-delay:0.15s]" />
                      <span className="h-1.5 w-1.5 animate-breathe rounded-full bg-paper-300 [animation-delay:0.3s]" />
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {errorMsg && (
          <div className="mx-8 mb-2 rounded-lg bg-crimson-500/10 px-3.5 py-2 text-sm text-crimson-400">{errorMsg}</div>
        )}

        <div className="border-t border-ink-700 px-8 py-4">
          <div className="mx-auto flex max-w-2xl items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              rows={1}
              placeholder="Ask about your documents…"
              className="flex-1 resize-none rounded-lg border border-ink-600 bg-ink-800 px-3.5 py-2.5 text-sm text-paper-100 placeholder:text-paper-300/50 outline-none focus:border-rose-500"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || queryMutation.isPending}
              className="flex h-[42px] w-[42px] flex-shrink-0 items-center justify-center rounded-lg bg-rose-500 text-ink-950 hover:bg-rose-400 disabled:opacity-40"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
