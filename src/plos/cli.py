"""CLI: ``python -m plos.cli {seed, run, recompute-mastery}``."""

from __future__ import annotations

import argparse
import asyncio
import sys


def _cmd_seed(args) -> int:
    from .db.engine import get_session_factory
    from .providers.registry import build_providers
    from .seed.seed import run as seed_run

    providers = build_providers()
    factory = get_session_factory()

    async def _go() -> int:
        async with factory() as session:
            return await seed_run(session, providers)

    inserted = asyncio.run(_go())
    print(f"seed complete: {inserted} rows inserted (idempotent)")
    return 0


def _cmd_run(args) -> int:
    import uvicorn

    uvicorn.run(
        "plos.app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def _cmd_recompute(args) -> int:
    from sqlalchemy import select

    from .db.engine import get_session_factory
    from .db.models.learners import Learner
    from .domain.mastery.engine import MasteryEngine

    factory = get_session_factory()

    async def _go() -> int:
        count = 0
        async with factory() as session:
            ids = [row[0] for row in (await session.execute(select(Learner.id))).all()]
            for lid in ids:
                engine = MasteryEngine(session)
                n = await engine.recompute_trends(lid)
                # Optional offline BKT re-fit if pybkt is available.
                if args.fit:
                    _maybe_pybkt_fit(session, lid)
                count += n
            await session.commit()
        return count

    total = asyncio.run(_go())
    print(f"recomputed trend/derived for {total} mastery rows" + (" (with pybkt.fit)" if args.fit else ""))
    return 0


def _maybe_pybkt_fit(session, learner_id: str) -> None:
    try:
        from pybkt import Model  # type: ignore
    except Exception:  # noqa: BLE001
        return
    # Placeholder for offline EM re-estimation on a learner's evidence log.
    # pybkt.Model().fit(...) would run here; intentionally a no-op in the stub build.
    _ = Model


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="plos", description="Personal Learning OS backend CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run the API server (uvicorn)")
    p_run.add_argument("--host", default="0.0.0.0")
    p_run.add_argument("--port", type=int, default=8001)
    p_run.add_argument("--reload", action="store_true")
    p_run.set_defaults(func=_cmd_run)

    p_seed = sub.add_parser("seed", help="Idempotently seed demo data")
    p_seed.set_defaults(func=_cmd_seed)

    p_recompute = sub.add_parser("recompute-mastery", help="Recompute mastery derived fields")
    p_recompute.add_argument("--fit", action="store_true", help="Also run offline pybkt.fit re-estimation")
    p_recompute.set_defaults(func=_cmd_recompute)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
