import { mockApi } from "./mock";
import type {
  ChatMessage,
  ChatThread,
  ErrorBookItem,
  KnowledgeBase,
  LearnerPreferences,
  LearnerState,
  MemoryItem,
  PlosApi,
  PersonaId,
  Question,
  QuizResult,
  SkillMeta,
  SkillRequest,
  SkillResult,
} from "./types";

/**
 * API client factory.
 *
 * The demo defaults to the in-memory MOCK backend (NEXT_PUBLIC_USE_MOCK !== "false"),
 * so it runs with zero external services. Set NEXT_PUBLIC_USE_MOCK=false and point
 * NEXT_PUBLIC_API_BASE_URL at a DeepTutor instance to hit the REAL client below.
 *
 * The REAL client is a thin fetch wrapper whose endpoints are the PLOS protocol
 * documented in docs/API协议.md (DeepTutor-native endpoints + the small PLOS
 * extension surface for LearnerState / Skills / MasteryEngine). When the PLOS
 * extension service is implemented, the real client works without changes here.
 */

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:3782";
export const LEARNER_ID = "stu_001";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return (await res.json()) as T;
}

const JSON_HEADERS = { "Content-Type": "application/json" } as const;

/** Real backend client — talks to the DeepTutor origin (proxies /api → FastAPI :8001). */
class RealApi implements PlosApi {
  private u(path: string) {
    return `${API_BASE_URL}${path}`;
  }

  async getLearnerState(id: string) {
    return json<LearnerState>(await fetch(this.u(`/api/learners/${id}/state`)));
  }

  async updatePreferences(id: string, prefs: Partial<LearnerPreferences>) {
    return json<LearnerState>(
      await fetch(this.u(`/api/learners/${id}/preferences`), {
        method: "PATCH",
        headers: JSON_HEADERS,
        body: JSON.stringify(prefs),
      })
    );
  }

  async listSkills() {
    return json<SkillMeta[]>(await fetch(this.u(`/api/skills`)));
  }

  async invokeSkill(req: SkillRequest) {
    return json<SkillResult>(
      await fetch(this.u(`/api/skills/invoke`), {
        method: "POST",
        headers: JSON_HEADERS,
        body: JSON.stringify(req),
      })
    );
  }

  async listThreads(id: string) {
    return json<ChatThread[]>(await fetch(this.u(`/api/learners/${id}/threads`)));
  }

  async getThread(_id: string, threadId: string) {
    return json<ChatThread>(await fetch(this.u(`/api/threads/${threadId}`)));
  }

  async sendMessage(id: string, threadId: string, content: string, persona: PersonaId) {
    // Note: real DeepTutor chat streams via /ws/chat. This REST fallback returns the
    // finalized assistant message; the production chat surface uses the WS client.
    return json<ChatMessage>(
      await fetch(this.u(`/api/threads/${threadId}/messages`), {
        method: "POST",
        headers: JSON_HEADERS,
        body: JSON.stringify({ learnerId: id, content, persona }),
      })
    );
  }

  async listKnowledgeBases(_id: string) {
    return json<KnowledgeBase[]>(await fetch(this.u(`/api/kbs`)));
  }

  async generateQuiz(id: string, topic: string, count: number) {
    return json<Question[]>(
      await fetch(this.u(`/api/quiz/generate`), {
        method: "POST",
        headers: JSON_HEADERS,
        body: JSON.stringify({ learnerId: id, topic, count }),
      })
    );
  }

  async gradeAnswer(id: string, question: Question, userAnswer: string) {
    return json<QuizResult>(
      await fetch(this.u(`/api/quiz/grade`), {
        method: "POST",
        headers: JSON_HEADERS,
        body: JSON.stringify({ learnerId: id, question, userAnswer }),
      })
    );
  }

  async listErrorBook(id: string) {
    return json<ErrorBookItem[]>(await fetch(this.u(`/api/learners/${id}/errors`)));
  }

  async listMemory(id: string) {
    return json<MemoryItem[]>(await fetch(this.u(`/api/learners/${id}/memory`)));
  }
}

export const api: PlosApi = USE_MOCK ? mockApi : new RealApi();
export const IS_MOCK = USE_MOCK;
