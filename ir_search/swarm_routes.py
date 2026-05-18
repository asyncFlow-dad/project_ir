from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SwarmRoute:
    condition: str
    target: str


# Routing table from deep-research-report § Swarm 라우팅 정책
ROUTING_TABLE: tuple[SwarmRoute, ...] = (
    SwarmRoute("PM Bot input", "PM Planner (+ Dev/QA fan-out when needed)"),
    SwarmRoute("Dev Bot technical query", "Dev subgraph (PM merge if blast radius is large)"),
    SwarmRoute("QA Bot benchmark/eval", "QA subgraph (Dev if retriever change proposed)"),
    SwarmRoute("document ingest event", "Dev pipeline (skip PM)"),
    SwarmRoute("release candidate eval", "QA -> PM approval"),
)


def route_request(*, requester_bot: str, intent: str) -> str:
    bot = requester_bot.lower()
    normalized = intent.lower()

    if "ingest" in normalized or "index" in normalized:
        return "dev-pipeline"
    if "benchmark" in normalized or "eval" in normalized:
        return "qa-subgraph" if bot != "pm" else "pm-planner"
    if bot == "pm":
        return "pm-planner"
    if bot == "qa":
        return "qa-subgraph"
    if bot == "dev":
        if any(token in normalized for token in ("deploy", "release", "breaking")):
            return "pm-merge"
        return "dev-subgraph"
    return "pm-planner"
