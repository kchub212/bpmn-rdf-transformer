from dataclasses import dataclass, field
@dataclass(frozen=True)
class StartEvent:
    id: str
    name: str | None = None

@dataclass(frozen=True)
class EndEvent:
    id: str
    name: str | None = None

@dataclass(frozen=True)
class Task:
    id: str
    name: str | None = None

@dataclass(frozen=True)
class ExclusiveGateway:
    id: str
    name: str | None = None

@dataclass(frozen=True)
class SequenceFlow:
    id: str
    source_ref: str
    target_ref: str
    name: str | None = None


FlowNode = StartEvent | EndEvent | Task | ExclusiveGateway


@dataclass
class Process:
    id: str
    name: str | None = None
    nodes: dict[str, FlowNode] = field(default_factory=dict)
    sequence_flows: list[SequenceFlow] = field(default_factory=list)
