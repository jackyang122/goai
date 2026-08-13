"""Static seed data — mirrors ``web/lib/api/seed.ts`` so the live backend serves the same
demo content the frontend was built against (stu_001 renders identically)."""

from __future__ import annotations

from typing import Dict, List

# ── Six skills (meta) ──────────────────────────────────────────────────────────
SKILL_METAS: List[dict] = [
    {"id": "learning-plan", "name": "学习规划", "description": "根据目标、可用时间与当前掌握度生成每日学习轨道。", "reads": ["mastery", "goals", "preferences"], "writes": ["goals"]},
    {"id": "homework-coach", "name": "作业辅导", "description": "对题目或材料给出分步提示，引导而非直接给答案。", "reads": ["mastery", "preferences"], "writes": ["recentActivity"]},
    {"id": "error-diagnosis", "name": "错因诊断", "description": "诊断错题根因并生成针对性讲解，写入薄弱点。", "reads": ["mastery"], "writes": ["weakPoints", "mastery"]},
    {"id": "personal-explain", "name": "个性化讲解", "description": "依据掌握度与偏好分层、换角度讲解概念。", "reads": ["mastery", "preferences"], "writes": ["recentActivity"]},
    {"id": "adaptive-practice", "name": "自适应练习", "description": "按薄弱点与掌握度生成难度自适应的题目序列。", "reads": ["mastery", "weakPoints"], "writes": ["mastery"]},
    {"id": "mistake-summary", "name": "错题归纳", "description": "周期性归类错题、提炼错误模式，刷新掌握度。", "reads": ["weakPoints"], "writes": ["mastery", "weakPoints"]},
]

# ── Learner + mastery + goal + tasks + cards + activity + preferences ─────────
LEARNER_ID = "stu_001"

LEARNER: dict = {
    "id": LEARNER_ID,
    "name": "同学",
    "streak": 4,
    "study_time_today_min": 25,
    "study_time_total_min": 1840,
    "weekly_change": 0.06,
    "session_count": 38,
    "weekly_question_count": 56,
    "preferences": {"persona": "teacher", "difficulty": "adaptive", "dailyGoalMin": 45, "language": "zh-CN"},
}

MASTERY: List[dict] = [
    {"id": "m_quad", "topic": "二次函数", "subject": "数学", "level": 0.42, "trend": "up", "last_practiced_at": "2026-08-09T13:20:00Z", "error_count": 7},
    {"id": "m_geo", "topic": "几何证明", "subject": "数学", "level": 0.46, "trend": "flat", "last_practiced_at": "2026-08-08T11:00:00Z", "error_count": 5},
    {"id": "m_tense", "topic": "时态辨析", "subject": "英语", "level": 0.63, "trend": "up", "last_practiced_at": "2026-08-09T09:10:00Z", "error_count": 3},
    {"id": "m_reading", "topic": "阅读理解", "subject": "英语", "level": 0.71, "trend": "up", "last_practiced_at": "2026-08-09T09:40:00Z", "error_count": 2},
    {"id": "m_phys", "topic": "牛顿第二定律", "subject": "物理", "level": 0.80, "trend": "up", "last_practiced_at": "2026-08-07T15:00:00Z", "error_count": 1},
]

# BKT params per topic; 二次函数 uses the design-doc UC-B params (T=0.10,S=0.30,G=0.30,L0=0.55).
MASTERY_PARAMS: Dict[str, dict] = {
    "二次函数": {"l0": 0.55, "t_transit": 0.10, "slip": 0.30, "guess": 0.30},
    "default": {"l0": 0.5, "t_transit": 0.1, "slip": 0.2, "guess": 0.2},
}

GOAL: dict = {
    "id": "goal_math", "title": "本周数学冲刺", "subject": "数学", "progress": 0.63,
    "deadline": "2026-08-17", "source": "learning-plan",
}
PLAN_TASKS: List[dict] = [
    {"id": "t1", "title": "二次函数 · 精通路径", "est_minutes": 20, "type": "learn", "done": False, "ref": {"kind": "book", "id": "book_quadratic"}, "ordering": 0},
    {"id": "t2", "title": "英语阅读 · 精读 1 篇", "est_minutes": 20, "type": "learn", "done": False, "ref": {"kind": "book", "id": "book_reading"}, "ordering": 1},
    {"id": "t3", "title": "错题重练 · 3 道薄弱", "est_minutes": 15, "type": "review", "done": False, "ref": {"kind": "cards", "id": "cards_weak"}, "ordering": 2},
]

FLASH_CARDS: List[dict] = [
    {"id": f"card_{i}", "front": ["二次函数顶点坐标公式？", "现在完成时 vs 一般过去时？", "全等三角形判定定理？"][i % 3],
     "back": "顶点 (-b/2a, (4ac-b²)/4a) — 对 y=ax²+bx+c；判别式 Δ=b²-4ac 决定与 x 轴交点数。",
     "topic": ["二次函数", "时态辨析", "几何证明"][i % 3], "due": "2026-08-10T12:00:00Z"}
    for i in range(12)
]

ACTIVITIES: List[dict] = [
    {"id": "a1", "type": "practice", "label": "完成《二次函数》小测 8 题", "ts": "2026-08-09T13:20:00Z"},
    {"id": "a2", "type": "learn", "label": "阅读《牛顿第二定律》智能教材", "ts": "2026-08-07T15:00:00Z"},
    {"id": "a3", "type": "review", "label": "复习 12 张闪卡", "ts": "2026-08-09T09:40:00Z"},
    {"id": "a4", "type": "chat", "label": "与 Teacher 讨论几何证明思路", "ts": "2026-08-08T11:00:00Z"},
]

# ── Question bank (topic → questions) ─────────────────────────────────────────
QUESTION_BANK: Dict[str, List[dict]] = {
    "二次函数": [
        {"id": "q1", "type": "choice", "prompt": "抛物线 y = x² - 4x + 3 的顶点坐标是？", "options": ["(2, -1)", "(2, 1)", "(-2, -1)", "(4, 3)"], "answer": "(2, -1)", "explanation": "x = -b/2a = 4/2 = 2；代入得 y = 4 - 8 + 3 = -1，故顶点 (2, -1)。", "topic": "二次函数", "skill": "adaptive-practice"},
        {"id": "q2", "type": "fill", "prompt": "函数 y = -x² 的开口向 ____（上/下）。", "answer": "下", "explanation": "二次项系数 a < 0 时抛物线开口向下。", "topic": "二次函数", "skill": "adaptive-practice"},
        {"id": "q3", "type": "choice", "prompt": "判别式 Δ = b² - 4ac < 0 时，抛物线与 x 轴的交点个数是？", "options": ["0", "1", "2", "无穷多"], "answer": "0", "explanation": "Δ < 0 表示方程无实数根，即与 x 轴无交点。", "topic": "二次函数", "skill": "adaptive-practice"},
    ],
    "几何证明": [
        {"id": "q4", "type": "choice", "prompt": "下列不能判定两个三角形全等的是？", "options": ["SSS", "SAS", "ASA", "SSA"], "answer": "SSA", "explanation": "SSA 在一般情况下不能唯一确定三角形，故不是全等判定定理。", "topic": "几何证明", "skill": "adaptive-practice"},
    ],
    "时态辨析": [
        {"id": "q5", "type": "choice", "prompt": "He ___ (live) here since 2010. 正确填空是？", "options": ["has lived", "lived", "is living", "lives"], "answer": "has lived", "explanation": "since 2010 搭配现在完成时，表示从过去持续到现在。", "topic": "时态辨析", "skill": "adaptive-practice"},
    ],
}

# ── Error book ────────────────────────────────────────────────────────────────
ERROR_BOOK: List[dict] = [
    {"id": "err1", "question": QUESTION_BANK["二次函数"][0], "user_answer": "(2, 1)", "error_type": "符号错误", "ts": "2026-08-09T13:22:00Z", "reviewed": False},
    {"id": "err2", "question": QUESTION_BANK["二次函数"][2], "user_answer": "2", "error_type": "概念混淆", "ts": "2026-08-09T13:24:00Z", "reviewed": False},
]

# ── Knowledge bases ───────────────────────────────────────────────────────────
KNOWLEDGE_BASES: List[dict] = [
    {"id": "kb_math", "name": "数学核心知识库", "engine": "llamaindex", "document_count": 24, "status": "ready", "created_at": "2026-07-20T10:00:00Z"},
    {"id": "kb_english", "name": "英语语料库", "engine": "pageindex", "document_count": 41, "status": "ready", "created_at": "2026-07-22T10:00:00Z"},
    {"id": "kb_research", "name": "课题研究 Vault", "engine": "obsidian", "document_count": 67, "status": "indexing", "created_at": "2026-08-09T18:00:00Z"},
]

# A canonical reference chunk for the math KB (so RAG retrieval has something to find).
KB_MATH_CHUNKS: List[dict] = [
    {"id": "kd1", "kb_id": "kb_math", "title": "二次函数.pdf", "chunk_index": 0,
     "content": "二次函数 y=ax²+bx+c 的顶点坐标为 (-b/2a, (4ac-b²)/4a)；对称轴为 x=-b/2a。判别式 Δ=b²-4ac 决定与 x 轴交点个数：>0 两个，=0 一个，<0 无。",
     "locator": "p.4"},
    {"id": "kd2", "kb_id": "kb_math", "title": "二次函数.pdf", "chunk_index": 1,
     "content": "当 a>0 时抛物线开口向上，顶点为最低点；a<0 时开口向下，顶点为最高点。配方 y=a(x-h)²+k 的顶点为 (h,k)。",
     "locator": "p.5"},
]

# ── Memory (three layers) ────────────────────────────────────────────────────
MEMORY_ITEMS: List[dict] = [
    {"id": "mem1", "layer": "L1", "content": "学生在「二次函数顶点坐标」上连续答错 3 次，常把 -b/2a 写成 b/2a。", "source": "session:2026-08-09", "created_at": "2026-08-09T13:25:00Z", "topic": "二次函数"},
    {"id": "mem2", "layer": "L2", "content": "学生擅长代数运算，弱于符号方向与正负号细节。", "source": "synthesis:error-diagnosis", "created_at": "2026-08-09T13:26:00Z", "topic": "二次函数"},
    {"id": "mem3", "layer": "L3", "content": "整体策略：先补「符号与正负号」类薄弱点，再推进函数综合应用。", "source": "synthesis:cross-surface", "created_at": "2026-08-10T08:00:00Z"},
]

# ── Threads ───────────────────────────────────────────────────────────────────
THREADS: List[dict] = [
    {
        "id": "thread_1", "title": "二次函数顶点怎么求？", "persona": "teacher",
        "created_at": "2026-08-09T13:00:00Z", "updated_at": "2026-08-09T13:30:00Z",
        "messages": [
            {"id": "msg_1", "role": "user", "content": "二次函数的顶点坐标怎么求？我老是算错。", "created_at": "2026-08-09T13:00:00Z", "skill": None, "status": "complete"},
            {"id": "msg_2", "role": "assistant", "skill": "personal-explain",
             "content": "我们一步步来。对 y = ax² + bx + c，顶点的横坐标固定为 x = -b/2a，纵坐标再代回求 y。\n\n你常把 -b/2a 写成 b/2a，关键就在这个负号——它是公式的一部分。建议先单独写一步：x = -b/2a，再代入。",
             "citations": [{"id": "c1", "source": "数学核心知识库 · 二次函数.pdf p.4", "snippet": "顶点公式：(-b/2a, (4ac-b²)/4a)"}],
             "status": "complete", "created_at": "2026-08-09T13:00:30Z"},
        ],
    }
]
