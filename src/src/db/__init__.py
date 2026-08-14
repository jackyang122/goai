"""Database layer: async SQLAlchemy 2 engine, declarative base, repositories.

The repository classes are the ONLY components that emit SQL. Higher layers depend on
repository interfaces, never on raw sessions in endpoint handlers.
"""
