from __future__ import annotations

from dataclasses import dataclass

STREAM_INBOX = "swarm.inbox"
STREAM_DEV = "swarm.dev"
STREAM_QA = "swarm.qa"
STREAM_PM = "swarm.pm"
STREAM_EVENTS = "swarm.events"

STREAM_CONSUMERS: dict[str, list[str]] = {
    STREAM_INBOX: ["router"],
    STREAM_DEV: ["dev-worker-1", "dev-worker-2"],
    STREAM_QA: ["qa-worker-1"],
    STREAM_PM: ["pm-worker-1"],
    STREAM_EVENTS: ["audit", "notifier"],
}


@dataclass(frozen=True)
class SwarmMessage:
    trace_id: str
    task_id: str
    role: str
    project_id: str
    conversation_id: str
    requester_bot: str
    priority: str
    payload_ref: str
    state_ref: str

    def to_fields(self) -> dict[str, str]:
        return {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "role": self.role,
            "project_id": self.project_id,
            "conversation_id": self.conversation_id,
            "requester_bot": self.requester_bot,
            "priority": self.priority,
            "payload_ref": self.payload_ref,
            "state_ref": self.state_ref,
        }


def all_streams() -> tuple[str, ...]:
    return tuple(STREAM_CONSUMERS.keys())
