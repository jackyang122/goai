"""MCP server — exposes the PLOS skills as Model Context Protocol tools.

Lets agents (Hermes Agent, Claude Code, …) call the six PLOS skills directly over
stdio, without the REST backend running. Start it with::

    uv run plos mcp

Then register it with your MCP client, e.g. for Claude Code / Hermes:

    "mcpServers": {
        "plos": {"command": "uv", "args": ["run", "plos", "mcp"]}
    }
"""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager

from mcp.server.fastmcp import Context, FastMCP

from .core.config import settings
from .core.logging import configure_logging, get_logger
from .db.base import Base
from .db.engine import dispose_engine, ensure_extensions, get_engine, get_session_factory
from .domain.learner_state import LearnerStateService
from .domain.skills.base import SkillContext
from .domain.skills.router import SkillRouter
from .providers.registry import build_providers

log = get_logger(__name__)

_router = SkillRouter()


@asynccontextmanager
async def _lifespan(mcp: FastMCP):
    """Mirror the app lifespan: providers, DB schema, idempotent seed."""
    configure_logging("DEBUG" if settings.debug else "INFO", stream=sys.stderr)
    providers = build_providers()
    factory = get_session_factory()

    try:
        await ensure_extensions()
        if settings.auto_create_tables:
            engine = get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # noqa: BLE001
        log.warning("DB schema setup skipped (is Postgres reachable?): %s", exc)

    if settings.seed_on_start:
        try:
            from .seed.seed import run as seed_run

            async with factory() as session:
                await seed_run(session, providers)
        except Exception as exc:  # noqa: BLE001
            log.warning("seed skipped: %s", exc)

    yield {"providers": providers, "session_factory": factory}
    await dispose_engine()


mcp = FastMCP("plos", lifespan=_lifespan)


async def _invoke(ctx: Context, learner_id: str, skill_id: str, inputs: dict):
    """Build a SkillContext (same shape as api/skills.py) and run the skill."""
    lc = ctx.request_context.lifespan_context
    factory = lc["session_factory"]
    providers = lc["providers"]

    async with factory() as session:
        try:
            state = await LearnerStateService(session).get_state(learner_id)
        except Exception:  # noqa: BLE001
            state = None
        skill_ctx = SkillContext(
            session=session,
            learner_id=learner_id,
            skill_id=skill_id,
            input=inputs,
            providers=providers,
            learner_state=state,
        )
        return await _router.invoke(skill_ctx)


def _render(result) -> str:
    return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)


@mcp.tool()
async def plos_learning_plan(
    ctx: Context,
    learner_id: str = "stu_001",
    available_min: int = 55,
) -> str:
    """根据当前掌握度与薄弱点生成每日学习轨道（learning-plan 技能）。"""
    return _render(await _invoke(ctx, learner_id, "learning-plan", {"availableMin": available_min}))


@mcp.tool()
async def plos_homework_coach(
    ctx: Context,
    learner_id: str = "stu_001",
    material: str = "",
) -> str:
    """对题目给出苏格拉底式分步提示，引导而非直接给答案（homework-coach 技能）。"""
    return _render(await _invoke(ctx, learner_id, "homework-coach", {"material": material}))


@mcp.tool()
async def plos_error_diagnosis(
    ctx: Context,
    learner_id: str = "stu_001",
    question: str = "",
    user_answer: str = "",
) -> str:
    """诊断错题根因并生成针对性讲解，写入薄弱点（error-diagnosis 技能）。"""
    return _render(
        await _invoke(ctx, learner_id, "error-diagnosis", {"question": question, "userAnswer": user_answer})
    )


@mcp.tool()
async def plos_personal_explain(
    ctx: Context,
    learner_id: str = "stu_001",
    concept: str = "二次函数顶点",
) -> str:
    """依据掌握度分层、换角度讲解一个概念，公式用 LaTeX（personal-explain 技能）。"""
    return _render(await _invoke(ctx, learner_id, "personal-explain", {"concept": concept}))


@mcp.tool()
async def plos_adaptive_practice(
    ctx: Context,
    learner_id: str = "stu_001",
    topic: str = "",
    count: int = 3,
) -> str:
    """按薄弱点与掌握度生成难度自适应的题目序列（adaptive-practice 技能）。"""
    return _render(await _invoke(ctx, learner_id, "adaptive-practice", {"topic": topic, "count": count}))


@mcp.tool()
async def plos_mistake_summary(
    ctx: Context,
    learner_id: str = "stu_001",
) -> str:
    """周期性归类错题、提炼错误模式并刷新掌握度（mistake-summary 技能）。"""
    return _render(await _invoke(ctx, learner_id, "mistake-summary", {}))
