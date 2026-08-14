"""Pagination helper.

List endpoints return a bare array by default (the frontend reads arrays). Only when the
caller passes ``?limit=`` (and optionally ``?cursor=``) do we wrap in ``{items,nextCursor}``.
"""

from __future__ import annotations

from typing import Any, List, Optional


def maybe_page(rows: List[Any], limit: Optional[int], cursor: Optional[str]) -> Any:
    if limit is None:
        return rows
    next_cursor = rows[-1].id if (limit and len(rows) >= limit and rows) else None
    return {"items": rows, "nextCursor": next_cursor}
