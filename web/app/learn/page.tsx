"use client";

import { useState } from "react";
import { BookOpen, FileText, Layers, NotebookPen, RotateCw, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useLearnerState } from "@/lib/hooks";
import { cn } from "@/lib/utils";

type Tab = "book" | "reader" | "notebook" | "cards";
const TABS: { id: Tab; label: string; icon: typeof BookOpen }[] = [
  { id: "book", label: "智能教材", icon: BookOpen },
  { id: "reader", label: "阅读", icon: FileText },
  { id: "notebook", label: "笔记本", icon: NotebookPen },
  { id: "cards", label: "闪卡", icon: Layers },
];

export default function LearnPage() {
  const [tab, setTab] = useState<Tab>("book");
  const { state, loading } = useLearnerState();

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4 md:p-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">学习</h1>
        <p className="mt-1 text-sm text-muted-foreground">沉浸式学习体验 · 智能教材、阅读、笔记与闪卡。</p>
      </div>

      <div className="flex gap-1 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              tab === t.id
                ? "border-accent text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {tab === "book" && <BookTab />}
      {tab === "reader" && <ReaderTab />}
      {tab === "notebook" && <NotebookTab />}
      {tab === "cards" && <CardsTab cards={state?.dueCards ?? []} loading={loading} />}
    </div>
  );
}

function BookTab() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Badge tone="accent" className="gap-1">
          <Sparkles className="h-3 w-3" /> AI 生成
        </Badge>
        <span className="text-sm text-muted-foreground">二次函数 · 第 3 章</span>
      </div>

      <article className="prose-reading space-y-4">
        <h2 className="text-xl font-semibold">§3.2 二次函数的顶点与对称轴</h2>
        <p>
          任意二次函数 <code className="rounded bg-muted px-1.5 py-0.5 text-sm">y = ax² + bx + c (a ≠ 0)</code> 的图象都是抛物线。
          其对称轴是直线 <code className="rounded bg-muted px-1.5 py-0.5 text-sm">x = -b/2a</code>，顶点坐标为{" "}
          <code className="rounded bg-muted px-1.5 py-0.5 text-sm">(-b/2a, (4ac-b²)/4a)</code>。
        </p>

        {/* Formula block */}
        <Card className="bg-muted/30">
          <CardContent className="p-4">
            <div className="mb-1 text-xs font-medium text-muted-foreground">公式</div>
            <div className="font-mono text-base">x = -b / 2a　　顶点 (-b/2a, c - b²/4a)</div>
          </CardContent>
        </Card>

        <p>
          当 a &gt; 0 时抛物线开口向上，顶点是最低点；当 a &lt; 0 时开口向下，顶点是最高点。
          判别式 Δ = b² - 4ac 决定抛物线与 x 轴交点的个数。
        </p>
      </article>

      {/* Inline quiz block */}
      <Card className="border-accent/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Sparkles className="h-4 w-4 text-accent" /> 随堂检测
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <p>抛物线 y = x² - 4x + 3 的顶点坐标是？</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {["(2, -1)", "(2, 1)", "(-2, -1)"].map((o) => (
              <span key={o} className="rounded-md border border-border px-3 py-1.5">
                {o}
              </span>
            ))}
          </div>
          <p className="mt-3 text-xs text-muted-foreground">在「练习」中答这类题并自动批改。</p>
        </CardContent>
      </Card>
    </div>
  );
}

function ReaderTab() {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="text-sm">二次函数.pdf · 第 4 页</CardTitle>
          <Badge tone="outline">React-PDF 预览</Badge>
        </CardHeader>
        <CardContent>
          <div className="prose-reading space-y-3 text-sm">
            <p className="rounded-md bg-accent/10 px-2 py-1">
              顶点公式：(-b/2a, (4ac-b²)/4a) — 这一句被选中后可在右侧向 AI 提问。
            </p>
            <p>
              在实际应用中，常通过配方法将一般式化为顶点式 y = a(x - h)² + k，其中 (h, k) 即顶点。
              顶点式便于直接读出抛物线的顶点与开口方向。
            </p>
            <p>
              例如 y = 2(x - 1)² + 3 的顶点为 (1, 3)，开口向上；而 y = -(x + 2)² - 1 的顶点为 (-2, -1)，开口向下。
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Sparkles className="h-4 w-4 text-accent" /> AI 侧栏
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="rounded-md bg-secondary p-3">
            <div className="mb-1 text-xs font-medium">选中：顶点公式</div>
            <p className="text-muted-foreground">
              这是抛物线最关键的公式。横坐标永远是 -b/2a，纵坐标代回即可。要我出一道配套练习吗？
            </p>
          </div>
          <Button variant="outline" size="sm" className="w-full">讲解这一段</Button>
        </CardContent>
      </Card>
    </div>
  );
}

function NotebookTab() {
  const notes = [
    { id: "n1", title: "二次函数顶点记忆法", snippet: "先写 x = -b/2a，再代回求 y。负号属于公式本身。" },
    { id: "n2", title: "全等三角形判定", snippet: "SSS / SAS / ASA / AAS；SSA 不成立。" },
    { id: "n3", title: "现在完成时触发词", snippet: "since / for / already / yet → 现在完成时。" },
  ];
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {notes.map((n) => (
        <Card key={n.id}>
          <CardContent className="p-4">
            <div className="mb-1 flex items-center gap-2">
              <NotebookPen className="h-4 w-4 text-accent" />
              <span className="text-sm font-medium">{n.title}</span>
            </div>
            <p className="text-sm text-muted-foreground">{n.snippet}</p>
          </CardContent>
        </Card>
      ))}
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center gap-2 p-6 text-center">
          <p className="text-sm text-muted-foreground">从对话中一键保存笔记，构建你的知识体系。</p>
          <Button variant="outline" size="sm">+ 新建笔记</Button>
        </CardContent>
      </Card>
    </div>
  );
}

function CardsTab({ cards, loading }: { cards: { id: string; front: string; back: string; topic: string }[]; loading: boolean }) {
  const [flipped, setFlipped] = useState<Record<string, boolean>>({});
  if (loading) return <Skeleton className="h-40" />;
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{cards.length} 张待复习闪卡 · 点击卡片翻转。</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.slice(0, 6).map((c) => {
          const isFlipped = flipped[c.id];
          return (
            <button
              key={c.id}
              onClick={() => setFlipped((f) => ({ ...f, [c.id]: !f[c.id] }))}
              className="relative h-44 text-left"
            >
              <Card className="flex h-full flex-col p-4 transition-colors hover:border-accent/40">
                <div className="mb-2 flex items-center justify-between">
                  <Badge tone="outline">{c.topic}</Badge>
                  <RotateCw className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
                {!isFlipped ? (
                  <div className="flex flex-1 items-center">
                    <p className="text-sm font-medium">{c.front}</p>
                  </div>
                ) : (
                  <div className="flex flex-1 items-center">
                    <p className="text-sm text-muted-foreground">{c.back}</p>
                  </div>
                )}
                <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                  {isFlipped ? "答案" : "问题"}
                </span>
              </Card>
            </button>
          );
        })}
      </div>
    </div>
  );
}
