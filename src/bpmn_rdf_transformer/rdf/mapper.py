import uuid

from rdflib import Graph, Namespace, Literal, RDF

from bpmn_rdf_transformer.model.process import (
    StartEvent,
    EndEvent,
    Task,
    ExclusiveGateway,
    Process,
)
from bpmn_rdf_transformer.parser.validation import validate_process

SBPMNC = Namespace("https://sBPMN.github.io/2.0/classes#")
SBPMNP = Namespace("https://sBPMN.github.io/2.0/properties#")
INSTANCE_BASE = "http://bpmn-rdf-transformer.org/instance/"


def node_class(node):
    if isinstance(node, StartEvent):
        return SBPMNC.startEvent
    elif isinstance(node, EndEvent):
        return SBPMNC.endEvent
    elif isinstance(node, Task):
        return SBPMNC.task
    elif isinstance(node, ExclusiveGateway):
        return SBPMNC.exclusiveGateway

#crl again !!
def to_rdf(process: Process) -> Graph:
    validate_process(process)

    graph = Graph()
    graph.bind("sbpmnc", SBPMNC)
    graph.bind("sbpmnp", SBPMNP)

    instance_ns = Namespace(f"{INSTANCE_BASE}{uuid.uuid4()}/")
    graph.bind("proc", instance_ns)
#bind proc !!
    process_uri = instance_ns[f"process/{process.id}"]
    graph.add((process_uri, RDF.type, SBPMNC.process))
    graph.add((process_uri, SBPMNP.id, Literal(process.id)))
    if process.name is not None:
        graph.add((process_uri, SBPMNP.name, Literal(process.name)))

    for node in process.nodes.values():
        node_uri = instance_ns[f"element/{node.id}"]
        graph.add((node_uri, RDF.type, node_class(node)))
        graph.add((node_uri, SBPMNP.id, Literal(node.id)))
        if node.name is not None:
            graph.add((node_uri, SBPMNP.name, Literal(node.name)))
        graph.add((process_uri, SBPMNP.flowElement, node_uri))

    for flow in process.sequence_flows:
        flow_uri = instance_ns[f"element/{flow.id}"]
        graph.add((flow_uri, RDF.type, SBPMNC.sequenceFlow))
        graph.add((flow_uri, SBPMNP.id, Literal(flow.id)))
        if flow.name is not None:
            graph.add((flow_uri, SBPMNP.name, Literal(flow.name)))
        graph.add((flow_uri, SBPMNP.sourceRef, instance_ns[f"element/{flow.source_ref}"]))
        graph.add((flow_uri, SBPMNP.targetRef, instance_ns[f"element/{flow.target_ref}"]))
        graph.add((process_uri, SBPMNP.flowElement, flow_uri))

    return graph
