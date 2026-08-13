"""Pydantic schemas — a 1:1 mirror of ``web/lib/api/types.ts``.

Field names are kept in camelCase so the JSON wire format is byte-for-byte the frontend
contract. Extensions flagged in the design doc (``ChatMessage.payload`` discriminated
union, ``QuizResult.score``, memory graph/write, card review) live here too.
"""
