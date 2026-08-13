"use client";

import { useEffect, useState } from "react";
import {
  Brain,
  Database,
  Layers3,
  Save,
  Settings as SettingsIcon,
  Sparkles,
  Wrench,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, LEARNER_ID } from "@/lib/api";
import type { KnowledgeBase, MemoryItem, SkillMeta } from "@/lib/api";
import { useLearnerState } from "@/lib/hooks";
import { cn } from "@/lib/utils";

type Tab = "kb" | "memory" | "skills" | "settings";
const TABS: { id: Tab; label: string; icon: typeof Database }[] = [
  { id: "kb", label: "知识库", icon: Database },
  { id: "memory", label: "记忆系统", icon: Brain },
  { id: "skills", label: "技能", icon: Wrench },
  { id: "settings", label: "设置", icon: SettingsIcon },
];

export default function MePage() {
  const [tab, setTab] = useState<Tab>("kb");
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [memory, setMemory] = useState<MemoryItem[]>([]);
  const [skills, setSkills] = useState<SkillMeta[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [k, m, s] = await Promise.all([
        api.listKnowledgeBases(LEARNER_ID),
        api.listMemory(LEARNER_ID),
        api.listSkills(),
      ]);
      setKbs(k);
      setMemory(m);
      setSkills(s);
      setLoading(false);
    })();
  }, []);

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4 md:p-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">我的</h1>
        <p className="mt-1 text-sm text-muted-foreground">知识库、记忆、技能与个性化设置。</p>
      </div>

      <div className="flex gap-1 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              tab === t.id ? "border-accent text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      ) : (
        <>
          {tab === "kb" && <KbTab kbs={kbs} />}
          {tab === "memory" && <MemoryTab memory={memory} />}
          {tab === "skills" && <SkillsTab skills={skills} />}
          {tab === "settings" && <SettingsTab />}
        </>
      )}
    </div>
  );
}

function KbTab({ kbs }: { kbs: KnowledgeBase[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {kbs.map((kb) => (
        <Card key={kb.id}>
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-accent" />
                <span className="text-sm font-medium">{kb.name}</span>
              </div>
              <Badge tone={kb.status === "ready" ? "success" : kb.status === "indexing" ? "warning" : "danger"}>
                {kb.status === "ready" ? "就绪" : kb.status === "indexing" ? "索引中" : "错误"}
              </Badge>
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
              <Badge tone="outline">{kb.engine}</Badge>
              <span>{kb.documentCount} 个文档</span>
            </div>
          </CardContent>
        </Card>
      ))}
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center gap-2 p-6 text-center">
          <p className="text-sm text-muted-foreground">创建多引擎知识库（LlamaIndex / PageIndex / GraphRAG / LightRAG / Obsidian）。</p>
          <Button variant="outline" size="sm">+ 新建知识库</Button>
        </CardContent>
      </Card>
    </div>
  );
}

function MemoryTab({ memory }: { memory: MemoryItem[] }) {
  const layers = [
    { id: "L1" as const, title: "L1 · 追踪", desc: "会话级原始痕迹" },
    { id: "L2" as const, title: "L2 · 摘要", desc: "提炼后的事实" },
    { id: "L3" as const, title: "L3 · 综合", desc: "跨场景的策略" },
  ];
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {layers.map((l) => {
        const items = memory.filter((m) => m.layer === l.id);
        return (
          <Card key={l.id}>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Layers3 className="h-4 w-4 text-accent" /> {l.title}
              </CardTitle>
              <p className="text-xs text-muted-foreground">{l.desc}</p>
            </CardHeader>
            <CardContent className="space-y-2">
              {items.map((m) => (
                <div key={m.id} className="rounded-md border border-border p-2.5">
                  <p className="text-xs">{m.content}</p>
                  <p className="mt-1 text-[10px] text-muted-foreground">来源：{m.source}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function SkillsTab({ skills }: { skills: SkillMeta[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {skills.map((s) => (
        <Card key={s.id}>
          <CardContent className="p-5">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-accent" />
              <span className="text-sm font-medium">{s.name}</span>
              <Badge tone="outline" className="ml-auto font-mono text-[10px]">{s.id}</Badge>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{s.description}</p>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div>
                <div className="mb-1 text-muted-foreground">读</div>
                <div className="flex flex-wrap gap-1">
                  {s.reads.map((r) => (
                    <Badge key={r} tone="outline" className="text-[10px]">{r}</Badge>
                  ))}
                </div>
              </div>
              <div>
                <div className="mb-1 text-muted-foreground">写</div>
                <div className="flex flex-wrap gap-1">
                  {s.writes.map((w) => (
                    <Badge key={w} tone="accent" className="text-[10px]">{w}</Badge>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function SettingsTab() {
  const { state, refresh } = useLearnerState();
  const [difficulty, setDifficulty] = useState(state?.preferences.difficulty ?? "adaptive");
  const [dailyGoal, setDailyGoal] = useState(state?.preferences.dailyGoalMin ?? 45);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (state) {
      setDifficulty(state.preferences.difficulty);
      setDailyGoal(state.preferences.dailyGoalMin);
    }
  }, [state]);

  async function save() {
    setSaving(true);
    await api.updatePreferences(LEARNER_ID, { difficulty, dailyGoalMin: dailyGoal });
    await refresh();
    setSaving(false);
  }

  if (!state) return <Skeleton className="h-40" />;

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle className="text-sm">个性化设置</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <Field label="练习难度">
          <div className="flex gap-2">
            {(["adaptive", "easy", "normal", "hard"] as const).map((d) => (
              <button
                key={d}
                onClick={() => setDifficulty(d)}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-sm transition-colors",
                  difficulty === d ? "border-accent bg-accent/10 text-accent" : "border-border hover:bg-muted"
                )}
              >
                {d}
              </button>
            ))}
          </div>
        </Field>

        <Field label={`每日目标：${dailyGoal} 分钟`}>
          <input
            type="range"
            min={15}
            max={120}
            step={5}
            value={dailyGoal}
            onChange={(e) => setDailyGoal(Number(e.target.value))}
            className="w-full accent-[hsl(var(--accent))]"
          />
        </Field>

        <Button variant="accent" onClick={save} disabled={saving} className="gap-1.5">
          <Save className="h-4 w-4" /> {saving ? "保存中…" : "保存"}
        </Button>
      </CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-2 text-sm font-medium">{label}</div>
      {children}
    </div>
  );
}
