/**
 * Personal Learning OS — Backend API contract (the "protocol").
 *
 * This file is the single source of truth for the data shapes exchanged between
 * the Next.js frontend and the backend. The demo ships a mock implementation
 * (`mock.ts`) that satisfies `PlosApi`; the real implementation talks to the
 * Personal Learning OS backend (FastAPI on :8001, proxied via the Next.js origin) plus a
 * thin PLOS extension service for LearnerState / Skills / MasteryEngine.
 *
 * See docs/API协议.md for the endpoint-by-endpoint mapping.
 */

// ─────────────────────────────────────────────────────────────────────────────
// Primitives
// ─────────────────────────────────────────────────────────────────────────────

export type PersonaId = "teacher";

export type Trend = "up" | "down" | "flat";

/** The six pluggable Learning Agent skills (PLOS extension over the Personal Learning OS backend). */
export type SkillId =
  | "learning-plan"
  | "homework-coach"
  | "error-diagnosis"
  | "personal-explain"
  | "adaptive-practice"
  | "mistake-summary";

export interface SkillMeta {
  id: SkillId;
  name: string;
  description: string;
  /** Declarative LearnerState fields this skill reads (for auditability). */
  reads: string[];
  /** Declarative LearnerState fields this skill writes (MasteryEngine is authoritative). */
  writes: string[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Learner State — the persistent core that flows through every module
// ─────────────────────────────────────────────────────────────────────────────

export interface MasteryPoint {
  id: string;
  topic: string;
  subject: string;
  /** 0..1 mastery level. */
  level: number;
  trend: Trend;
  lastPracticedAt: string;
  errorCount: number;
}

export interface PlanTask {
  id: string;
  title: string;
  estMinutes: number;
  type: "learn" | "practice" | "review";
  done: boolean;
  ref?: { kind: "book" | "quiz" | "cards"; id: string };
}

export interface Goal {
  id: string;
  title: string;
  subject: string;
  progress: number;
  deadline?: string;
  source: SkillId;
  tasks: PlanTask[];
}

export interface FlashCard {
  id: string;
  front: string;
  back: string;
  topic: string;
  due: string;
}

export interface Activity {
  id: string;
  type: "learn" | "practice" | "review" | "chat";
  label: string;
  ts: string;
}

export interface LearnerPreferences {
  persona: PersonaId;
  difficulty: "adaptive" | "easy" | "normal" | "hard";
  dailyGoalMin: number;
  language: string;
}

export interface LearnerState {
  learnerId: string;
  name: string;
  streak: number;
  studyTimeTodayMin: number;
  studyTimeTotalMin: number;
  /** Overall mastery across all topics (0..1), e.g. 0.71. */
  overallMastery: number;
  /** Mastery delta vs last week, e.g. 0.06 → "+6%". */
  weeklyChange: number;
  sessionCount: number;
  weeklyQuestionCount: number;
  goals: Goal[];
  mastery: MasteryPoint[];
  /** Derived: mastery points below the weak threshold (< 0.6). */
  weakPoints: MasteryPoint[];
  dueCards: FlashCard[];
  recentActivity: Activity[];
  preferences: LearnerPreferences;
  updatedAt: string;
}

/** A declarative patch over LearnerState produced as a skill side-effect. */
export type LearnerStateDelta = Partial<
  Pick<LearnerState, "mastery" | "weakPoints" | "goals" | "dueCards" | "recentActivity" | "studyTimeTodayMin">
>;

// ─────────────────────────────────────────────────────────────────────────────
// Skills — invocation contract
// ─────────────────────────────────────────────────────────────────────────────

export interface Citation {
  id: string;
  source: string;
  snippet: string;
  locator?: string;
}

export interface StepTrace {
  step: string;
  detail?: string;
}

export interface SkillRequest {
  skill: SkillId;
  learnerId: string;
  /** Skill-specific payload (see SkillInput maps in mock.ts). */
  input: Record<string, unknown>;
  context?: {
    kbIds?: string[];
    sessionId?: string;
    persona?: PersonaId;
  };
}

export interface SkillResult {
  skill: SkillId;
  /** Skill-specific payload. */
  output: Record<string, unknown>;
  /** Declarative LearnerState writes (MasteryEngine applies them). */
  sideEffects: LearnerStateDelta;
  citations?: Citation[];
  trace?: StepTrace[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Chat — message format aligned with assistant-ui's thread model
// ─────────────────────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant" | "system" | "tool";
export type MessageStatus = "streaming" | "complete" | "error";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
  citations?: Citation[];
  skill?: SkillId;
  status?: MessageStatus;
}

export interface ChatThread {
  id: string;
  title: string;
  persona: PersonaId;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Knowledge Base — multi-engine RAG
// ─────────────────────────────────────────────────────────────────────────────

export type KbEngine =
  | "llamaindex"
  | "pageindex"
  | "graphrag"
  | "lightrag"
  | "obsidian";

export type KbStatus = "ready" | "indexing" | "error";

export interface KnowledgeBase {
  id: string;
  name: string;
  engine: KbEngine;
  documentCount: number;
  status: KbStatus;
  createdAt: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Practice / Quiz
// ─────────────────────────────────────────────────────────────────────────────

export type QuestionType = "choice" | "fill" | "open";

export interface Question {
  id: string;
  type: QuestionType;
  prompt: string;
  options?: string[];
  answer: string;
  explanation: string;
  topic: string;
  skill?: SkillId;
}

export interface QuizResult {
  questionId: string;
  correct: boolean;
  userAnswer: string;
  topic: string;
}

export interface ErrorBookItem {
  id: string;
  question: Question;
  userAnswer: string;
  errorType: string;
  ts: string;
  reviewed: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// Memory — three-layer (L1/L2/L3)
// ─────────────────────────────────────────────────────────────────────────────

export type MemoryLayer = "L1" | "L2" | "L3";

export interface MemoryItem {
  id: string;
  layer: MemoryLayer;
  content: string;
  source: string;
  createdAt: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// The protocol surface — every backend (mock or real) implements this.
// ─────────────────────────────────────────────────────────────────────────────

export interface PlosApi {
  // Learner State
  getLearnerState(learnerId: string): Promise<LearnerState>;
  updatePreferences(
    learnerId: string,
    prefs: Partial<LearnerPreferences>
  ): Promise<LearnerState>;

  // Skills (unified agent entrypoint)
  invokeSkill(req: SkillRequest): Promise<SkillResult>;
  listSkills(): Promise<SkillMeta[]>;

  // Chat (assistant-ui compatible)
  listThreads(learnerId: string): Promise<ChatThread[]>;
  getThread(learnerId: string, threadId: string): Promise<ChatThread>;
  sendMessage(
    learnerId: string,
    threadId: string,
    content: string,
    persona: PersonaId
  ): Promise<ChatMessage>;

  // Knowledge Base
  listKnowledgeBases(learnerId: string): Promise<KnowledgeBase[]>;

  // Practice
  generateQuiz(learnerId: string, topic: string, count: number): Promise<Question[]>;
  gradeAnswer(learnerId: string, question: Question, userAnswer: string): Promise<QuizResult>;
  listErrorBook(learnerId: string): Promise<ErrorBookItem[]>;

  // Memory
  listMemory(learnerId: string): Promise<MemoryItem[]>;
}
