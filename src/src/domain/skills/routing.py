"""Keyword skill router + canned responder, mirroring ``web/lib/api/mock.ts``.

The canned text is the fallback used by the stub LLM and by the chat orchestrator when no
real LLM is configured, so the conversation surface behaves identically to the mock the
frontend was built against.
"""

from __future__ import annotations

import re

from ...schemas.common import SkillId


def pick_skill(text: str) -> SkillId:
    t = text.lower()
    if re.search(r"计划|安排|复习什么|今天学|该怎么学", text):
        return "learning-plan"
    if re.search(r"练习|做题|出题|quiz|刷题", t):
        return "adaptive-practice"
    if re.search(r"错题|错在哪|为什么错|错因", text):
        return "error-diagnosis"
    if re.search(r"归纳|总结错|错题本", text):
        return "mistake-summary"
    if re.search(r"作业|这道题|怎么做|帮我解", text):
        return "homework-coach"
    return "personal-explain"


def canned_reply(text: str) -> str:
    skill = pick_skill(text)
    if skill == "learning-plan":
        return (
            "根据你当前的掌握度，我建议今天的轨道是：\n\n"
            "1. 二次函数 · 精通路径（约 20 分钟）——你的掌握度 42%，重点补顶点与判别式\n"
            "2. 错题重练 · 3 道（约 15 分钟）——都是你最近错过的薄弱点\n"
            "3. 英语阅读 · 1 篇（约 20 分钟）——保持语感\n\n"
            "完成后整体掌握度预计提升到 ~73%。要现在开始第 1 项吗？"
        )
    if skill == "adaptive-practice":
        return (
            "好，我按你的薄弱点出 3 道自适应题（难度随你的掌握度调整）。"
            "先来第 1 题：抛物线 y = x² - 4x + 3 的顶点坐标是？"
        )
    if skill == "error-diagnosis":
        return (
            "我看了一下你的错题：核心是「符号错误」——把顶点横坐标 -b/2a 误写成 b/2a。\n\n"
            "关键点：公式里的负号属于公式本身，不是 a 或 b 的符号。\n"
            "我把它加入薄弱点，并安排 1 道针对练习巩固。"
        )
    if skill == "mistake-summary":
        return (
            "本周错题归纳：\n\n"
            "• 符号/正负号错误 — 5 次（二次函数顶点、不等式方向）\n"
            "• 概念混淆 — 2 次（判别式与交点个数）\n\n"
            "建议优先补「符号与正负号」类，预计 2 天可显著改善。"
        )
    if skill == "homework-coach":
        return (
            "我们分步来，先不急着想答案：\n\n"
            "1. 先确认这是什么类型的问题（函数？几何？）\n"
            "2. 把已知量列出来\n"
            "3. 想想哪个公式/定理和这些量相关\n\n"
            "你把题目贴上来，或者告诉我你卡在哪一步？"
        )
    # personal-explain
    return (
        "我用两种方式给你讲：\n\n"
        "• 直观：把它想成「先找到对称轴 x = -b/2a，再上下平移到顶点」。\n"
        "• 严格：配方 y = a(x + b/2a)² + (4ac-b²)/4a，顶点即 (-b/2a, (4ac-b²)/4a)。\n\n"
        "关键是记住横坐标永远是 -b/2a。要我再出一道配套练习检验一下吗？"
    )
