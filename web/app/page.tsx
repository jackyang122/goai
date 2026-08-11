"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Circle,
  Clock,
  Flame,
  Layers,
  ListChecks,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useLearnerState } from "@/lib/hooks";
import { cn, formatMinutes, masteryLabel, masteryTone } from "@/lib/utils";

const toneBar = { success: "bg-success", warning: "bg-warning", danger: "bg-danger" } as const;
const toneText = { success: "text-success", warning: "text-warning", danger: "text-danger" } as const;

function greeting() {
  const h = new Date().getHours();
  if (h < 6) return "凌晨好";
  if (h < 12) return "早上好";
  if (h < 14) return "中午好";
  if (h < 18) return "下午好";
  return "晚上好";
}

export default function DashboardPage() {
  const { state, loading } = useLearnerState();

  if (loading || !state) return <DashboardSkeleton />;

  const kpis = [
    {
      label: "今日学习",
      value: formatMinutes(state.studyTimeTodayMin),
      icon: Clock,
      hint: `目标 ${state.preferences.dailyGoalMin} 分钟`,
    },
    {
      label: "整体掌握",
      value: masteryLabel(state.overallMastery),
      icon: Target,
      hint: `本周 +${Math.round(state.weeklyChange * 100)}%`,
      trend: true,
    },
    {
      label: "本周题量",
      value: `${state.weeklyQuestionCount}`,
      icon: ListChecks,
      hint: "道题",
    },
    {
      label: "连续学习",
      value: `${state.streak}`,
      icon: Flame,
      hint: "天",
    },
  ];

  const tasks = state.goals[0]?.tasks ?? [];
  const doneCount = tasks.filter((t) => t.done).length;
  const weakest = state.weakPoints[0];
  const todayPlanPct = tasks.length ? (doneCount / tasks.length) * 100 : 0;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 md:p-8">
      {/* Greeting */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {greeting()}，{state.name} 👋
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            继续昨天的学习，今天还有 {tasks.length - doneCount} 项任务。
          </p>
        </div>
        <Badge tone="warning" className="gap-1.5 py-1">
          <Flame className="h-3.5 w-3.5" /> 连续 {state.streak} 天
        </Badge>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map((k) => (
          <Card key={k.label} className="overflow-hidden">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">{k.label}</span>
                <k.icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="mt-2 flex items-baseline gap-1.5">
                <span className="text-3xl font-semibold tracking-tight">{k.value}</span>
                {k.trend && (
                  <span className="flex items-center gap-0.5 text-xs font-medium text-success">
                    <TrendingUp className="h-3 w-3" />
                    {k.hint}
                  </span>
                )}
                {!k.trend && <span className="text-xs text-muted-foreground">{k.hint}</span>}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column */}
        <div className="space-y-6 lg:col-span-2">
          {/* Today's plan (learning-plan) */}
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-accent" />
                <CardTitle>今日推荐</CardTitle>
                <Badge tone="accent" className="ml-1">learning-plan</Badge>
              </div>
              <span className="text-xs text-muted-foreground">
                {doneCount}/{tasks.length} · {Math.round(todayPlanPct)}%
              </span>
            </CardHeader>
            <CardContent className="space-y-2">
              <Progress value={todayPlanPct} className="mb-3" />
              {tasks.map((t) => (
                <PlanTaskRow key={t.id} title={t.title} estMinutes={t.estMinutes} type={t.type} done={t.done} />
              ))}
            </CardContent>
          </Card>

          {/* Mastery Path */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-accent" />
                <CardTitle>Mastery Path 精通路径</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
                {state.mastery.map((m, i) => {
                  const tone = masteryTone(m.level);
                  return (
                    <div key={m.id} className="flex items-center">
                      <div className="w-36 shrink-0 rounded-lg border border-border p-3">
                        <div className="truncate text-sm font-medium">{m.topic}</div>
                        <div className="mt-1 text-xs text-muted-foreground">{m.subject}</div>
                        <div className={cn("mt-2 text-lg font-semibold", toneText[tone])}>
                          {masteryLabel(m.level)}
                        </div>
                        <Progress value={m.level * 100} indicatorClass={toneBar[tone]} className="mt-1.5 h-1.5" />
                      </div>
                      {i < state.mastery.length - 1 && (
                        <div className="mx-1 h-px w-4 bg-border" />
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* AI insight */}
          {weakest && (
            <Card className="border-accent/30 bg-accent/[0.03]">
              <CardContent className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
                <div className="flex gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent/15 text-accent">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-sm font-medium">
                      你的「{weakest.topic}」掌握度仅 {masteryLabel(weakest.level)}，错误集中在核心公式符号。
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      我安排了 3 道针对练习，预计 8 分钟可显著改善。
                    </p>
                    <Badge tone="outline" className="mt-2 gap-1">
                      来源：Memory L1 · session:2026-08-09
                    </Badge>
                  </div>
                </div>
                <Link href="/practice" className="shrink-0">
                  <Button variant="accent" className="gap-1.5">
                    开始练习 <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Due cards */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>待复习</CardTitle>
                <Badge tone="accent">{state.dueCards.length}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {state.dueCards.length} 张闪卡到期，建议现在复习以巩固记忆。
              </p>
              <Link href="/learn">
                <Button variant="outline" className="mt-3 w-full gap-1.5">
                  开始复习 <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Weak points */}
          <Card>
            <CardHeader>
              <CardTitle>薄弱知识点</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {state.weakPoints.map((m) => {
                const tone = masteryTone(m.level);
                return (
                  <div key={m.id}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="font-medium">{m.topic}</span>
                      <span className={cn("font-medium", toneText[tone])}>{masteryLabel(m.level)}</span>
                    </div>
                    <Progress value={m.level * 100} indicatorClass={toneBar[tone]} className="h-1.5" />
                  </div>
                );
              })}
              {state.weakPoints.length === 0 && (
                <p className="text-sm text-muted-foreground">暂无薄弱点，继续保持！</p>
              )}
            </CardContent>
          </Card>

          {/* Recent activity */}
          <Card>
            <CardHeader>
              <CardTitle>最近活动</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {state.recentActivity.slice(0, 4).map((a) => (
                <div key={a.id} className="flex items-start gap-3 text-sm">
                  <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-muted">
                    <ActivityIcon type={a.type} />
                  </div>
                  <div className="min-w-0">
                    <div className="truncate">{a.label}</div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(a.ts).toLocaleDateString("zh-CN", { month: "short", day: "numeric" })}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function PlanTaskRow({
  title,
  estMinutes,
  type,
  done,
}: {
  title: string;
  estMinutes: number;
  type: "learn" | "practice" | "review";
  done: boolean;
}) {
  const [checked, setChecked] = useState(done);
  const typeLabel = { learn: "学习", practice: "练习", review: "复习" }[type];
  return (
    <button
      onClick={() => setChecked((c) => !c)}
      className="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left transition-colors hover:bg-muted/60"
    >
      {checked ? (
        <CheckCircle2 className="h-5 w-5 shrink-0 text-success" />
      ) : (
        <Circle className="h-5 w-5 shrink-0 text-muted-foreground" />
      )}
      <span className={cn("flex-1 text-sm", checked && "text-muted-foreground line-through")}>
        {title}
      </span>
      <Badge tone="outline" className="hidden sm:inline-flex">{typeLabel}</Badge>
      <span className="flex items-center gap-1 text-xs text-muted-foreground">
        <Clock className="h-3 w-3" /> {estMinutes}m
      </span>
    </button>
  );
}

function ActivityIcon({ type }: { type: "learn" | "practice" | "review" | "chat" }) {
  const cls = "h-3.5 w-3.5 text-muted-foreground";
  if (type === "learn") return <BookOpen className={cls} />;
  if (type === "practice") return <ListChecks className={cls} />;
  if (type === "chat") return <Sparkles className={cls} />;
  return <Layers className={cls} />;
}

function DashboardSkeleton() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 md:p-8">
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Skeleton className="h-64 lg:col-span-2" />
        <Skeleton className="h-64" />
      </div>
    </div>
  );
}
