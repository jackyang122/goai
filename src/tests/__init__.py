"""DB-free test suite for the Personal Learning OS backend.

These tests exercise pure domain logic (BKT math, schema validation, semantic
grading, FSRS scheduling, skill routing, id format) without a database — so they
run anywhere `pytest` is installed. End-to-end tests requiring Postgres+pgvector
live elsewhere.
"""
