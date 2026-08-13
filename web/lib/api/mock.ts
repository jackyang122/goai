import {
  buildInitialThreads,
  buildLearnerState,
  ERROR_BOOK,
  KNOWLEDGE_BASES,
  MEMORY_ITEMS,
  QUESTION_BANK,
  SKILLS,
} from "./seed";
import type {
  ChatMessage,
  ChatThread,
  Citation,
  ErrorBookItem,
  KnowledgeBase,
  LearnerPreferences,
  LearnerState,
  MasteryPoint,
  MemoryItem,
  PlosApi,
  Question,
  QuizResult,
  SkillId,
  SkillMeta,
  SkillRequest,
  SkillResult,
} from "./types";
import { delay } from "@/lib/utils";

const WEAK_THRESHOLD = 0.6;

function deriveWeakPoints(mastery: MasteryPoint[]): MasteryPoint[] {
  return mastery.filter((m) => m.level < WEAK_THRESHOLD).sort((a, b) => a.level - b.level);
}

function nowIso(): string {
  return new Date().toISOString();
}

/** In-memory store backing the mock API. Reset on full page reload. */
class Store {
  states = new Map<string, LearnerState>();
  threads = new Map<string, ChatThread[]>();
  errorBooks = new Map<string, ErrorBookItem[]>();

  constructor() {
    const seed = buildLearnerState();
    seed.weakPoints = deriveWeakPoints(seed.mastery);
    this.states.set(seed.learnerId, seed);
    this.threads.set(seed.learnerId, buildInitialThreads());
    this.errorBooks.set(seed.learnerId, [...ERROR_BOOK]);
  }

  state(id: string): LearnerState {
    let s = this.states.get(id);
    if (!s) {
      s = buildLearnerState();
      s.learnerId = id;
      s.weakPoints = deriveWeakPoints(s.mastery);
      this.states.set(id, s);
    }
    return s;
  }
}

const store = new Store();

// ── Teacher-persona responder (keyword → skill, with citations) ──────────────

function pickSkill(text: string): SkillId {
  const t = text.toLowerCase();
  if (/(计划|安排|复习什么|今天学|该怎么学)/.test(text)) return "learning-plan";
  if (/(练习|做题|出题|quiz|刷题)/.test(t)) return "adaptive-practice";
  if (/(错题|错在哪|为什么错|错因)/.test(text)) return "error-diagnosis";
  if (/(归纳|总结错|错题本)/.test(text)) return "mistake-summary";
  if (/(作业|这道题|怎么做|帮我解)/.test(text)) return "homework-coach";
  return "personal-explain";
}

function respond(text: string): { content: string; citations: Citation[] } {
  const skill = pickSkill(text);

  const cit = (source: string, snippet: string): Citation => ({
    id: `c_${Math.random().toString(36).slice(2, 8)}`,
    source,
    snippet,
  });

  switch (skill) {
    case "learning-plan":
      return {
        content:
          
          "根据你当前的掌握度，我建议今天的轨道是：\n\n" +
          "1. 二次函数 · 精通路径（约 20 分钟）——你的掌握度 42%，重点补顶点与判别式\n" +
          "2. 错题重练 · 3 道（约 15 分钟）——都是你最近错过的薄弱点\n" +
          "3. 英语阅读 · 1 篇（约 20 分钟）——保持语感\n\n" +
          "完成后整体掌握度预计提升到 ~73%。要现在开始第 1 项吗？",
        citations: [cit("LearnerState · mastery[]", "二次函数 0.42 ▲｜几何证明 0.46 →")],
      };
    case "adaptive-practice":
      return {
        content:
          
          "好，我按你的薄弱点出 3 道自适应题（难度随你的掌握度调整）。" +
          "先来第 1 题：抛物线 y = x² - 4x + 3 的顶点坐标是？",
        citations: [cit("题库 · adaptive-practice", "topic=二次函数, base_level=0.42")],
      };
    case "error-diagnosis":
      return {
        content:
          
          "我看了一下你的错题：核心是「符号错误」——把顶点横坐标 -b/2a 误写成 b/2a。\n\n" +
          "关键点：公式里的负号属于公式本身，不是 a 或 b 的符号。\n" +
          "我把它加入薄弱点，并安排 1 道针对练习巩固。",
        citations: [cit("Memory L1 · session:2026-08-09", "符号错误 3 次，集中在 -b/2a")],
      };
    case "mistake-summary":
      return {
        content:
          
          "本周错题归纳：\n\n" +
          "• 符号/正负号错误 — 5 次（二次函数顶点、不等式方向）\n" +
          "• 概念混淆 — 2 次（判别式与交点个数）\n\n" +
          "建议优先补「符号与正负号」类，预计 2 天可显著改善。",
        citations: [cit("Memory L2 · synthesis:error-diagnosis", "弱于符号方向，擅长代数运算")],
      };
    case "homework-coach":
      return {
        content:
          
          "我们分步来，先不急着想答案：\n\n" +
          "1. 先确认这是什么类型的问题（函数？几何？）\n" +
          "2. 把已知量列出来\n" +
          "3. 想想哪个公式/定理和这些量相关\n\n" +
          "你把题目贴上来，或者告诉我你卡在哪一步？",
        citations: [],
      };
    default: // personal-explain
      return {
        content:
          
          "我用两种方式给你讲：\n\n" +
          "• 直观：把它想成「先找到对称轴 x = -b/2a，再上下平移到顶点」。\n" +
          "• 严格：配方 y = a(x + b/2a)² + (4ac-b²)/4a，顶点即 (-b/2a, (4ac-b²)/4a)。\n\n" +
          "关键是记住横坐标永远是 -b/2a。要我再出一道配套练习检验一下吗？",
        citations: [cit("数学核心知识库 · 二次函数.pdf p.4", "顶点 (-b/2a, (4ac-b²)/4a)")],
      };
  }
}

// ── Mock PlosApi implementation ──────────────────────────────────────────────

export const mockApi: PlosApi = {
  async getLearnerState(learnerId) {
    await delay(120);
    return clone(store.state(learnerId));
  },

  async updatePreferences(learnerId, prefs) {
    const s = store.state(learnerId);
    s.preferences = { ...s.preferences, ...prefs } as LearnerPreferences;
    s.updatedAt = nowIso();
    return clone(s);
  },

  async listSkills() {
    await delay(60);
    return SKILLS;
  },

  async invokeSkill(req: SkillRequest): Promise<SkillResult> {
    await delay(200);
    const s = store.state(req.learnerId);

    const recent = (label: string) => [
      { id: `act_${Date.now()}`, type: "chat" as const, label, ts: nowIso() },
      ...s.recentActivity,
    ].slice(0, 8);

    switch (req.skill) {
      case "learning-plan": {
        const tasks = s.goals[0]?.tasks ?? [];
        return {
          skill: "learning-plan",
          output: { plan: tasks, rationale: "基于当前掌握度与薄弱点生成" },
          sideEffects: {},
          trace: [{ step: "读取 mastery/goals" }, { step: "生成每日轨道" }],
        };
      }
      case "personal-explain": {
        const r = respond(String(req.input.concept ?? "二次函数顶点"));
        return {
          skill: "personal-explain",
          output: { explanation: r.content },
          sideEffects: { recentActivity: recent("个性化讲解：二次函数顶点") },
          citations: r.citations,
        };
      }
      case "adaptive-practice": {
        const topic = String(req.input.topic ?? s.weakPoints[0]?.topic ?? "二次函数");
        const qs = (QUESTION_BANK[topic] ?? QUESTION_BANK["二次函数"]).slice(
          0,
          Number(req.input.count ?? 3)
        );
        return {
          skill: "adaptive-practice",
          output: { questions: qs },
          sideEffects: {},
          trace: [{ step: `选题 topic=${topic}, base_level 检索` }],
        };
      }
      case "error-diagnosis": {
        const cause = "符号错误：将 -b/2a 误写为 b/2a";
        return {
          skill: "error-diagnosis",
          output: { cause, remedy: "强化公式中负号属于公式本身的记忆" },
          sideEffects: {
            weakPoints: s.weakPoints,
            mastery: s.mastery.map((m) =>
              m.topic === "二次函数" ? { ...m, errorCount: m.errorCount + 1 } : m
            ),
          },
          citations: [{ id: "c_err", source: "Memory L1", snippet: cause }],
        };
      }
      case "mistake-summary": {
        return {
          skill: "mistake-summary",
          output: {
            patterns: [
              { type: "符号/正负号", count: 5 },
              { type: "概念混淆", count: 2 },
            ],
          },
          sideEffects: { mastery: s.mastery, weakPoints: s.weakPoints },
          trace: [{ step: "聚类错题本" }, { step: "刷新 mastery" }],
        };
      }
      case "homework-coach": {
        return {
          skill: "homework-coach",
          output: { steps: ["识别题型", "列出已知量", "匹配公式/定理", "分步求解"] },
          sideEffects: { recentActivity: recent("作业辅导：分步提示") },
        };
      }
      default:
        return { skill: req.skill, output: {}, sideEffects: {} };
    }
  },

  async listThreads(learnerId) {
    await delay(80);
    return clone(store.threads.get(learnerId) ?? []);
  },

  async getThread(learnerId, threadId) {
    await delay(80);
    const t = (store.threads.get(learnerId) ?? []).find((x) => x.id === threadId);
    if (!t) throw new Error("thread not found");
    return clone(t);
  },

  async sendMessage(learnerId, threadId, content) {
    await delay(380);
    const threads = store.threads.get(learnerId) ?? [];
    let thread = threads.find((t) => t.id === threadId);
    if (!thread) {
      thread = {
        id: threadId,
        title: content.slice(0, 24),
        persona: "teacher",
        messages: [],
        createdAt: nowIso(),
        updatedAt: nowIso(),
      };
      threads.push(thread);
      store.threads.set(learnerId, threads);
    }

    const userMsg: ChatMessage = {
      id: `m_${Date.now()}_u`,
      role: "user",
      content,
      createdAt: nowIso(),
      status: "complete",
    };
    thread.messages.push(userMsg);

    const skill = pickSkill(content);
    const { content: reply, citations } = respond(content);
    const assistantMsg: ChatMessage = {
      id: `m_${Date.now()}_a`,
      role: "assistant",
      content: reply,
      skill,
      citations,
      createdAt: nowIso(),
      status: "complete",
    };
    thread.messages.push(assistantMsg);
    thread.updatedAt = nowIso();
    thread.persona = "teacher";

    return clone(assistantMsg);
  },

  async listKnowledgeBases(_learnerId) {
    await delay(100);
    return clone(KNOWLEDGE_BASES);
  },

  async generateQuiz(_learnerId, topic, count) {
    await delay(300);
    const bank = QUESTION_BANK[topic] ?? QUESTION_BANK["二次函数"];
    const out: Question[] = [];
    for (let i = 0; i < count; i++) out.push({ ...bank[i % bank.length], id: `${bank[i % bank.length].id}_${i}` });
    return out;
  },

  async gradeAnswer(learnerId, question, userAnswer) {
    await delay(150);
    const norm = (x: string) => x.trim().toLowerCase().replace(/[(),\s]/g, "");
    const correct = norm(userAnswer) === norm(question.answer);
    const s = store.state(learnerId);
    if (!correct) {
      const eb: ErrorBookItem[] = store.errorBooks.get(learnerId) ?? [];
      eb.unshift({
        id: `err_${Date.now()}`,
        question,
        userAnswer,
        errorType: "待诊断",
        ts: nowIso(),
        reviewed: false,
      });
      store.errorBooks.set(learnerId, eb);
    } else {
      // bump mastery a touch on correct answers (MasteryEngine behavior)
      s.mastery = s.mastery.map((m) =>
        m.topic === question.topic
          ? { ...m, level: Math.min(1, m.level + 0.02), trend: "up", lastPracticedAt: nowIso() }
          : m
      );
      s.weeklyQuestionCount += 1;
    }
    return { questionId: question.id, correct, userAnswer, topic: question.topic };
  },

  async listErrorBook(learnerId) {
    await delay(80);
    return clone(store.errorBooks.get(learnerId) ?? []);
  },

  async listMemory(_learnerId) {
    await delay(80);
    return clone(MEMORY_ITEMS);
  },
};

// trivial deep clone so callers can't mutate the store by reference
function clone<T>(v: T): T {
  return JSON.parse(JSON.stringify(v)) as T;
}

// Re-export type helpers for the client layer
export type { KnowledgeBase, MemoryItem, SkillMeta };
