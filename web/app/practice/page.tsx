"use client";

import { useEffect, useState } from "react";
import { BookX, CheckCircle2, Lightbulb, RefreshCw, Target, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, LEARNER_ID } from "@/lib/api";
import type { ErrorBookItem, Question, QuizResult } from "@/lib/api";
import { cn } from "@/lib/utils";
import { FEATURES } from "@/lib/features";

const TOPICS = ["二次函数", "几何证明", "时态辨析"];

export default function PracticePage() {
  // Feature-gated: hidden until FEATURES.practice is enabled (see lib/features.ts).
  // Render nothing feature-related before the flag check so hook order stays valid.
  if (!FEATURES.practice) {
    return <PracticeComingSoon />;
  }
  return <PracticeContent />;
}

function PracticeComingSoon() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col items-center justify-center gap-3 p-4 py-24 text-center md:p-8">
      <Target className="h-10 w-10 text-muted-foreground" />
      <h1 className="text-xl font-semibold">智能测验 · 即将上线</h1>
      <p className="text-sm text-muted-foreground">该功能正在开发中，敬请期待。</p>
    </div>
  );
}

function PracticeContent() {
  const [topic, setTopic] = useState("二次函数");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [results, setResults] = useState<Record<string, QuizResult>>({});
  const [submitted, setSubmitted] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [errorBook, setErrorBook] = useState<ErrorBookItem[]>([]);
  const [loadingBook, setLoadingBook] = useState(true);

  useEffect(() => {
    (async () => {
      setErrorBook(await api.listErrorBook(LEARNER_ID));
      setLoadingBook(false);
    })();
    generate("二次函数");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function generate(t: string) {
    setTopic(t);
    setGenerating(true);
    setSubmitted(false);
    setAnswers({});
    setResults({});
    const qs = await api.generateQuiz(LEARNER_ID, t, 3);
    setQuestions(qs);
    setGenerating(false);
  }

  async function submit() {
    const out: Record<string, QuizResult> = {};
    for (const q of questions) {
      out[q.id] = await api.gradeAnswer(LEARNER_ID, q, answers[q.id]?.trim() ?? "");
    }
    setResults(out);
    setSubmitted(true);
    setErrorBook(await api.listErrorBook(LEARNER_ID));
  }

  const score = Object.values(results).filter((r) => r.correct).length;
  const answeredCount = questions.filter((q) => answers[q.id]?.trim()).length;

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4 md:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">智能测验</h1>
          <p className="mt-1 text-sm text-muted-foreground">AI 从知识库生成题目，自动批改并收录错题。</p>
        </div>
        <div className="flex items-center gap-2">
          {TOPICS.map((t) => (
            <button
              key={t}
              onClick={() => generate(t)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                topic === t ? "border-accent bg-accent/10 text-accent" : "border-border text-muted-foreground hover:bg-muted"
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {submitted && (
        <Card className="border-accent/30 bg-accent/[0.03]">
          <CardContent className="flex items-center justify-between p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent/15 text-accent">
                <CheckCircle2 className="h-5 w-5" />
              </div>
              <div>
                <div className="text-sm font-medium">
                  本次得分 {score}/{questions.length}
                </div>
                <p className="text-xs text-muted-foreground">
                  {score === questions.length ? "全部正确，继续保持！" : "已将错题收录至错题本，可针对性复习。"}
                </p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={() => generate(topic)} className="gap-1.5">
              <RefreshCw className="h-3.5 w-3.5" /> 再练一组
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Questions */}
      <div className="space-y-4">
        {generating ? (
          <Skeleton className="h-40" />
        ) : (
          questions.map((q, i) => (
            <QuestionCard
              key={q.id}
              index={i + 1}
              question={q}
              value={answers[q.id] ?? ""}
              onChange={(v) => setAnswers((a) => ({ ...a, [q.id]: v }))}
              result={results[q.id]}
              submitted={submitted}
            />
          ))
        )}
      </div>

      {!generating && questions.length > 0 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            已作答 {answeredCount}/{questions.length}
          </span>
          <Button variant="accent" onClick={submit} disabled={submitted} className="gap-1.5">
            <CheckCircle2 className="h-4 w-4" /> 提交并批改
          </Button>
        </div>
      )}

      {/* Error book */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <BookX className="h-4 w-4 text-danger" />
            <CardTitle>错题本</CardTitle>
            <Badge tone="danger">{errorBook.length}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {loadingBook ? (
            <Skeleton className="h-16" />
          ) : errorBook.length === 0 ? (
            <p className="text-sm text-muted-foreground">还没有错题，去练一组吧。</p>
          ) : (
            errorBook.map((e) => (
              <div key={e.id} className="rounded-md border border-border p-3">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-medium">{e.question.prompt}</p>
                  <Badge tone="danger" className="shrink-0">{e.errorType}</Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  你的答案：<span className="text-danger">{e.userAnswer || "（未作答）"}</span> · 正确：{e.question.answer}
                </p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function QuestionCard({
  index,
  question,
  value,
  onChange,
  result,
  submitted,
}: {
  index: number;
  question: Question;
  value: string;
  onChange: (v: string) => void;
  result?: QuizResult;
  submitted: boolean;
}) {
  const correct = result?.correct;
  return (
    <Card className={cn(submitted && (correct ? "border-success/40" : "border-danger/40"))}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="mb-2 flex items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground">第 {index} 题</span>
              <Badge tone="outline">{question.type === "choice" ? "选择" : question.type === "fill" ? "填空" : "问答"}</Badge>
              <Badge tone="outline">{question.topic}</Badge>
            </div>
            <p className="text-[15px] font-medium leading-relaxed">{question.prompt}</p>
          </div>
          {submitted &&
            (correct ? (
              <CheckCircle2 className="h-5 w-5 shrink-0 text-success" />
            ) : (
              <XCircle className="h-5 w-5 shrink-0 text-danger" />
            ))}
        </div>

        <div className="mt-4">
          {question.type === "choice" && question.options ? (
            <div className="space-y-2">
              {question.options.map((opt) => {
                const chosen = value === opt;
                const isAnswer = opt === question.answer;
                return (
                  <button
                    key={opt}
                    disabled={submitted}
                    onClick={() => onChange(opt)}
                    className={cn(
                      "flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm transition-colors",
                      submitted && isAnswer
                        ? "border-success/50 bg-success/10"
                        : submitted && chosen && !isAnswer
                        ? "border-danger/50 bg-danger/10"
                        : chosen
                        ? "border-accent bg-accent/10"
                        : "border-border hover:bg-muted"
                    )}
                  >
                    <span className="font-medium">{opt}</span>
                  </button>
                );
              })}
            </div>
          ) : (
            <input
              value={value}
              disabled={submitted}
              onChange={(e) => onChange(e.target.value)}
              placeholder="输入你的答案"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
            />
          )}
        </div>

        {submitted && (
          <div className="mt-3 flex gap-2 rounded-md bg-muted/50 p-3 text-sm">
            <Lightbulb className="h-4 w-4 shrink-0 text-warning" />
            <div>
              <span className="font-medium">解析：</span>
              <span className="text-muted-foreground">{question.explanation}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
