from rdflib import Graph, RDF

from bpmn_rdf_transformer.rdf.mapper import SBPMNC, SBPMNP


# Explicit sBPMN class hierarchy (from ADR 0006), written out by hand instead of
# using a generic OWL reasoner (owlrl), since only these six concrete classes
# ever occur in graphs produced by this project.
HIERARCHY = {
    SBPMNC.process: [SBPMNC.callableElement, SBPMNC.rootElement, SBPMNC.baseElement],
    SBPMNC.task: [SBPMNC.activity, SBPMNC.flowNode, SBPMNC.flowElement, SBPMNC.baseElement],
    SBPMNC.startEvent: [
        SBPMNC.catchEvent,
        SBPMNC.event,
        SBPMNC.flowNode,
        SBPMNC.flowElement,
        SBPMNC.baseElement,
    ],
    SBPMNC.endEvent: [
        SBPMNC.throwEvent,
        SBPMNC.event,
        SBPMNC.flowNode,
        SBPMNC.flowElement,
        SBPMNC.baseElement,
    ],
    SBPMNC.exclusiveGateway: [
        SBPMNC.gateway,
        SBPMNC.flowNode,
        SBPMNC.flowElement,
        SBPMNC.baseElement,
    ],
    SBPMNC.sequenceFlow: [SBPMNC.flowElement, SBPMNC.baseElement],
}


MIN_GATEWAY_OUTGOING_FLOWS = 2


def improve_rdf(graph: Graph) -> tuple[Graph, list[str]]:
    warnings = []

    # Modeling warning: an ExclusiveGateway with fewer than 2 outgoing flows
    # isn't really branching. This is a warning, not an error - the graph stays valid.
    for gateway in graph.subjects(RDF.type, SBPMNC.exclusiveGateway):
        outgoing_flows = list(graph.subjects(SBPMNP.sourceRef, gateway))
        if len(outgoing_flows) < MIN_GATEWAY_OUTGOING_FLOWS:
            warnings.append(
                f"{gateway}: ExclusiveGateway hat nur {len(outgoing_flows)} "
                f"ausgehende(n) SequenceFlow(s), erwartet werden mindestens "
                f"{MIN_GATEWAY_OUTGOING_FLOWS}"
            )

    # Silent enrichment: fill in implied superclass types. Nothing here is ever
    # wrong, so none of this is reported as a warning.
    for concrete_class, superclasses in HIERARCHY.items():
        for resource in list(graph.subjects(RDF.type, concrete_class)):
            for superclass in superclasses:
                triple = (resource, RDF.type, superclass)
                if triple not in graph:
                    graph.add(triple)

    return graph, warnings
