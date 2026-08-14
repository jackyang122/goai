"use client";

import { useEffect, useRef, useState } from "react";
import {
  GraduationCap,
  Paperclip,
  Send,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, LEARNER_ID, API_BASE_URL } from "@/lib/api";
import type { ChatMessage } from "@/lib/api";
import { cn } from "@/lib/utils";

const SUGGESTIONS = ["帮我规划今天的复习", "二次函数顶点怎么求？", "出一道二次函数的练习题", "总结我这周错题的规律"];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const threadId = useRef("thread_demo");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    (async () => {
      const threads = await api.listThreads(LEARNER_ID);
      if (threads[0]) {
        threadId.current = threads[0].id;
        setMessages(threads[0].messages);
      }
      setLoading(false);
    })();
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    const content = text.trim();
    if (!content || sending) return;
    setInput("");
    const userMsg: ChatMessage = {
      id: `u_${Date.now()}`,
      role: "user",
      content,
      createdAt: new Date().toISOString(),
      status: "complete",
    };
    setMessages((m) => [...m, userMsg]);
    setSending(true);

    const wsUrl = API_BASE_URL.replace(/^http/, "ws") + "/ws/chat";
    const ws = new WebSocket(wsUrl);
    let assistantMsg: ChatMessage | null = null;

    ws.onopen = () => {
      ws.send(JSON.stringify({
        threadId: threadId.current,
        learnerId: LEARNER_ID,
        content,
        persona: "teacher",
      }));
    };

    ws.onmessage = (event) => {
      try {
        const ev = JSON.parse(event.data);
        if (ev.type === "content" && ev.delta) {
          if (!assistantMsg) {
            assistantMsg = {
              id: `a_${Date.now()}`,
              role: "assistant",
              content: "",
              createdAt: new Date().toISOString(),
              status: "streaming",
            };
            setMessages((m) => [...m, assistantMsg!]);
          }
          assistantMsg.content += ev.delta;
          // Force re-render by replacing the last message
          setMessages((m) => {
            const next = [...m];
            next[next.length - 1] = { ...assistantMsg! };
            return next;
          });
        } else if (ev.type === "skill") {
          // Skill detection — could show a badge
        } else if (ev.type === "done") {
          if (assistantMsg) {
            assistantMsg.status = "complete";
            assistantMsg.id = ev.messageId || assistantMsg.id;
            setMessages((m) => {
              const next = [...m];
              next[next.length - 1] = { ...assistantMsg! };
              return next;
            });
          }
          ws.close();
          setSending(false);
        } else if (ev.type === "error") {
          console.error("WS error:", ev.message);
          ws.close();
          setSending(false);
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => {
      // Fallback to REST if WebSocket fails
      ws.close();
      api.sendMessage(LEARNER_ID, threadId.current, content, "teacher")
        .then((reply) => setMessages((m) => [...m, reply]))
        .finally(() => setSending(false));
    };

    ws.onclose = () => {
      setSending(false);
    };
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-4rem)] max-w-3xl flex-col px-4 py-4 md:px-8">
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto scrollbar-thin">
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-16 w-3/4" />
            <Skeleton className="h-24 w-3/4" />
          </div>
        ) : (
          messages.map((m) => <MessageBubble key={m.id} message={m} />)
        )}
        {sending && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4 animate-pulse text-accent" />
            讲师正在思考…
          </div>
        )}
        {messages.length === 0 && !loading && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-accent/10 text-accent">
              <GraduationCap className="h-6 w-6" />
            </div>
            <p className="text-sm text-muted-foreground">向你的讲师提问，开始学习。</p>
          </div>
        )}
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Composer */}
      <Card className="flex items-end gap-2 p-2">
        <Button variant="ghost" size="icon" className="shrink-0" aria-label="附件">
          <Paperclip className="h-4 w-4" />
        </Button>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
          rows={1}
          placeholder="问任何问题…  (Enter 发送，Shift+Enter 换行)"
          className="max-h-32 flex-1 resize-none bg-transparent px-1 py-2 text-sm outline-none placeholder:text-muted-foreground"
        />
        <Button variant="accent" size="icon" className="shrink-0" disabled={!input.trim() || sending} onClick={() => send(input)}>
          <Send className="h-4 w-4" />
        </Button>
      </Card>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isStreaming = message.status === "streaming";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div className={cn("max-w-[85%] space-y-2", isUser ? "items-end" : "items-start")}>
        {!isUser && message.skill && (
          <Badge tone="accent" className="gap-1">
            <Sparkles className="h-3 w-3" /> {message.skill}
          </Badge>
        )}
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "rounded-br-sm bg-primary text-primary-foreground"
              : "rounded-bl-sm bg-secondary text-secondary-foreground",
            isStreaming && "animate-pulse"
          )}
        >
          <div className="whitespace-pre-wrap">{message.content}</div>
          {isStreaming && message.content === "" && (
            <span className="inline-flex gap-0.5">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" style={{ animationDelay: "0ms" }} />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" style={{ animationDelay: "150ms" }} />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" style={{ animationDelay: "300ms" }} />
            </span>
          )}
          {isStreaming && message.content !== "" && (
            <span className="ml-0.5 inline-block h-4 w-1 animate-pulse bg-accent" />
          )}
        </div>
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="space-y-1">
            {message.citations.map((c) => (
              <div key={c.id} className="rounded-md border border-border bg-muted/40 px-2.5 py-1.5 text-xs">
                <span className="font-medium text-foreground">📎 {c.source}</span>
                <p className="mt-0.5 text-muted-foreground">{c.snippet}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}