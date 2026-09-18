from rdflib import Graph, RDF

from bpmn_rdf_transformer.exceptions import RdfValidationError
from bpmn_rdf_transformer.model.process import (
    StartEvent,
    EndEvent,
    Task,
    ExclusiveGateway,
    SequenceFlow,
    Process,
)
from bpmn_rdf_transformer.parser.validation import validate_process
from bpmn_rdf_transformer.rdf.mapper import SBPMNC, SBPMNP
from bpmn_rdf_transformer.rdf.validation import validate_rdf


NODE_CLASSES = {
    SBPMNC.startEvent: StartEvent,
    SBPMNC.endEvent: EndEvent,
    SBPMNC.task: Task,
    SBPMNC.exclusiveGateway: ExclusiveGateway,
}


def _optional_literal(graph: Graph, subject, prop) -> str | None:
    value = next(graph.objects(subject, prop), None)
    return str(value) if value is not None else None


def from_rdf(graph: Graph) -> Process:
    validate_rdf(graph)

    process_uris = list(graph.subjects(RDF.type, SBPMNC.process))
    if len(process_uris) != 1:
        raise RdfValidationError(
            f"Erwartet genau einen sbpmnc:process im Graph, {len(process_uris)} gefunden"
        )
    process_uri = process_uris[0]

    process = Process(
        id=str(next(graph.objects(process_uri, SBPMNP.id))),
        name=_optional_literal(graph, process_uri, SBPMNP.name),
    )

    for element in graph.objects(process_uri, SBPMNP.flowElement):
        types = set(graph.objects(element, RDF.type))

        # Checked against the concrete node classes only, so an sBPMN superclass
        # triple added by improve_rdf() (e.g. flowNode, baseElement) never
        # interferes with detecting the real leaf type.
        node_class = next((cls for t, cls in NODE_CLASSES.items() if t in types), None)
        if node_class is not None:
            node = node_class(
                id=str(next(graph.objects(element, SBPMNP.id))),
                name=_optional_literal(graph, element, SBPMNP.name),
            )
            process.nodes[node.id] = node
            continue

        if SBPMNC.sequenceFlow in types:
            source_uri = next(graph.objects(element, SBPMNP.sourceRef))
            target_uri = next(graph.objects(element, SBPMNP.targetRef))
            flow = SequenceFlow(
                id=str(next(graph.objects(element, SBPMNP.id))),
                source_ref=str(next(graph.objects(source_uri, SBPMNP.id))),
                target_ref=str(next(graph.objects(target_uri, SBPMNP.id))),
                name=_optional_literal(graph, element, SBPMNP.name),
            )
            process.sequence_flows.append(flow)

    validate_process(process)
    return process
