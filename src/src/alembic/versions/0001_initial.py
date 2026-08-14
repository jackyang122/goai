"""initial schema (all tables + pgvector HNSW indexes)

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-13

Self-contained: creates the pgvector extension, then all PLOS tables matching the ORM in
``src.db.models``. The embedding dimension is parameterized (BGE-M3 = 1024).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

from src.core.config import settings

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DIM = settings.embedding_dim


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "learners",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False, server_default="同学"),
        sa.Column("streak", sa.Integer, server_default="0"),
        sa.Column("study_time_today_min", sa.Integer, server_default="0"),
        sa.Column("study_time_today_date", sa.Date, nullable=True),
        sa.Column("study_time_total_min", sa.Integer, server_default="0"),
        sa.Column("weekly_change", sa.Float, server_default="0"),
        sa.Column("session_count", sa.Integer, server_default="0"),
        sa.Column("weekly_question_count", sa.Integer, server_default="0"),
        sa.Column("preferences", sa.dialects.postgresql.JSONB, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "mastery",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("learner_id", sa.String, sa.ForeignKey("learners.id"), nullable=False),
        sa.Column("topic", sa.String, nullable=False),
        sa.Column("subject", sa.String, server_default=""),
        sa.Column("level", sa.Float, server_default="0.0"),
        sa.Column("trend", sa.String, server_default="flat"),
        sa.Column("error_count", sa.Integer, server_default="0"),
        sa.Column("last_practiced_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("level BETWEEN 0 AND 1", name="ck_mastery_level"),
        sa.UniqueConstraint("learner_id", "topic", name="uq_mastery_learner_topic"),
    )
    op.create_index("ix_mastery_learner_id", "mastery", ["learner_id"])
    op.create_index("ix_mastery_topic", "mastery", ["topic"])

    op.create_table(
        "mastery_params",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("learner_id", sa.String, sa.ForeignKey("learners.id"), nullable=False),
        sa.Column("topic", sa.String, nullable=False),
        sa.Column("l0", sa.Float, server_default="0.5"),
        sa.Column("t_transit", sa.Float, server_default="0.1"),
        sa.Column("slip", sa.Float, server_default="0.2"),
        sa.Column("guess", sa.Float, server_default="0.2"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("learner_id", "topic", name="uq_mastery_params_topic"),
    )
    op.create_index("ix_mastery_params_learner_id", "mastery_params", ["learner_id"])

    op.create_table(
        "goals",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("learner_id", sa.String, sa.ForeignKey("learners.id"), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("subject", sa.String, server_default=""),
        sa.Column("progress", sa.Float, server_default="0"),
        sa.Column("deadline", sa.Date, nullable=True),
        sa.Column("source", sa.String, server_default="learning-plan"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_goals_learner_id", "goals", ["learner_id"])

    op.create_table(
        "plan_tasks",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("goal_id", sa.String, sa.ForeignKey("goals.id"), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("est_minutes", sa.Integer, server_default="0"),
        sa.Column("type", sa.String, server_default="learn"),
        sa.Column("done", sa.Boolean, server_default="false"),
        sa.Column("ref", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("ordering", sa.Integer, server_default="0"),
    )
    op.create_index("ix_plan_tasks_goal_id", "plan_tasks", ["goal_id"])

    op.create_table(
        "questions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("options", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("explanation", sa.Text, server_default=""),
        sa.Column("topic", sa.String, nullable=False),
        sa.Column("skill", sa.String, nullable=True),
    )
    op.create_index("ix_questions_topic", "questions", ["topic"])

    op.create_table(
        "error_book",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("learner_id", sa.String, sa.ForeignKey("learners.id"), nullable=False),
        sa.Column("question_id", sa.String, nullable=True),
        sa.Column("question_snapshot", sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column("user_answer", sa.Text, nullable=False),
        sa.Column("error_type", sa.String, server_default="待诊断"),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed", sa.Boolean, server_default="false"),
    )
    op.create_index("ix_error_book_learner_id", "error_book", ["learner_id"])
    op.create_index("ix_error_book_ts", "error_book", ["ts"])

    op.create_table(
        "flash_cards",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("learner_id", sa.String, sa.ForeignKey("learners.id"), nullable=False),
        sa.Column("front", sa.Text, nullable=False),
        sa.Column("back", sa.Text, nullable=False),
        sa.Column("topic", sa.String, nullable=False),
        sa.Column("due", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stability", sa.Float, nullable=True),
        sa.Column("difficulty", sa.Float, nullable=True),
        sa.Column("state", sa.Integer, server_default="0"),
        sa.Column("reps", sa.Integer, server_default="0"),
        sa.Column("lapses", sa.Integer, server_default="0"),
        sa.Column("last_review", sa.DateTime(timezone=True), nullable=True),
        sa.Column("elapsed_days", sa.Integer, server_default="0"),
        sa.Column("scheduled_days", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_flash_cards_learner_id", "flash_cards", ["learner_id"])
    op.create_index("ix_flash_cards_due", "flash_cards", ["due"])
    op.create_index("ix_flash_cards_topic", "flash_cards", ["topic"])

    op.create_table(
        "threads",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("learner_id", sa.String, sa.ForeignKey("learners.id"), nullable=False),
        sa.Column("title", sa.Text, server_default=""),
        sa.Column("persona", sa.String, server_default="teacher"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("seq", sa.Integer, server_default="0"),
    )
    op.create_index("ix_threads_learner_id", "threads", ["learner_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("thread_id", sa.String, sa.ForeignKey("threads.id"), nullable=False),
        sa.Column("learner_id", sa.String, nullable=False),
        sa.Column("role", sa.String, nullable=False),
        sa.Column("content", sa.Text, server_default=""),
        sa.Column("skill", sa.String, nullable=True),
        sa.Column("status", sa.String, server_default="complete"),
        sa.Column("citations", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("payload", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("seq", sa.Integer, server_default="0"),
    )
    op.create_index("ix_messages_thread_id", "messages", ["thread_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])

    op.create_table(
        "attachments",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("thread_id", sa.String, sa.ForeignKey("threads.id"), nullable=False),
        sa.Column("learner_id", sa.String, nullable=False),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column("mime", sa.String, server_default="application/octet-stream"),
        sa.Column("size", sa.Integer, server_default="0"),
        sa.Column("storage_path", sa.Text, nullable=True),
        sa.Column("kb_id", sa.String, nullable=True),
        sa.Column("status", sa.String, server_default="indexing"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_attachments_thread_id", "attachments", ["thread_id"])

    op.create_table(
        "memory",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("learner_id", sa.String, sa.ForeignKey("learners.id"), nullable=False),
        sa.Column("layer", sa.String, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source", sa.String, server_default=""),
        sa.Column("topic", sa.String, nullable=True),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("evidence", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("embedding", Vector(DIM), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_memory_learner_id", "memory", ["learner_id"])
    op.create_index("ix_memory_layer", "memory", ["layer"])
    op.create_index("ix_memory_topic", "memory", ["topic"])
    op.create_index("ix_memory_created_at", "memory", ["created_at"])
    op.execute("CREATE INDEX ix_memory_embedding_hnsw ON memory USING hnsw (embedding vector_cosine_ops)")

    op.create_table(
        "memory_edge",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("learner_id", sa.String, nullable=False),
        sa.Column("src_memory_id", sa.String, sa.ForeignKey("memory.id"), nullable=False),
        sa.Column("dst_memory_id", sa.String, sa.ForeignKey("memory.id"), nullable=False),
        sa.Column("relation", sa.String, nullable=False),
        sa.Column("weight", sa.Float, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_memory_edge_learner_id", "memory_edge", ["learner_id"])
    op.create_index("ix_memory_edge_src", "memory_edge", ["src_memory_id"])
    op.create_index("ix_memory_edge_dst", "memory_edge", ["dst_memory_id"])

    op.create_table(
        "kb",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("owner_learner_id", sa.String, nullable=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("engine", sa.String, server_default="llamaindex"),
        sa.Column("document_count", sa.Integer, server_default="0"),
        sa.Column("status", sa.String, server_default="indexing"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_kb_owner_learner_id", "kb", ["owner_learner_id"])

    op.create_table(
        "kb_documents",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("kb_id", sa.String, sa.ForeignKey("kb.id"), nullable=False),
        sa.Column("title", sa.Text, server_default=""),
        sa.Column("chunk_index", sa.Integer, server_default="0"),
        sa.Column("embedding", Vector(DIM), nullable=True),
        sa.Column("content", sa.Text, server_default=""),
        sa.Column("locator", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_kb_documents_kb_id", "kb_documents", ["kb_id"])
    op.execute("CREATE INDEX ix_kb_documents_embedding_hnsw ON kb_documents USING hnsw (embedding vector_cosine_ops)")

    op.create_table(
        "activity",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("learner_id", sa.String, nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_activity_learner_id", "activity", ["learner_id"])
    op.create_index("ix_activity_ts", "activity", ["ts"])


def downgrade() -> None:
    for table in (
        "activity",
        "kb_documents",
        "kb",
        "memory_edge",
        "memory",
        "attachments",
        "messages",
        "threads",
        "flash_cards",
        "error_book",
        "questions",
        "plan_tasks",
        "goals",
        "mastery_params",
        "mastery",
        "learners",
    ):
        op.drop_table(table)
