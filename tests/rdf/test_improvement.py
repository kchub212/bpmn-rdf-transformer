from rdflib import RDF

from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_file
from bpmn_rdf_transformer.rdf.improvement import improve_rdf
from bpmn_rdf_transformer.rdf.mapper import SBPMNC, SBPMNP, to_rdf


def test_task_gets_full_hierarchy_added():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    graph, warnings = improve_rdf(graph)

    task_uri = next(graph.subjects(RDF.type, SBPMNC.task))
    assert (task_uri, RDF.type, SBPMNC.activity) in graph
    assert (task_uri, RDF.type, SBPMNC.flowNode) in graph
    assert (task_uri, RDF.type, SBPMNC.flowElement) in graph
    assert (task_uri, RDF.type, SBPMNC.baseElement) in graph
    assert warnings == []


def test_start_event_gets_event_hierarchy_added():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    graph, warnings = improve_rdf(graph)

    start_uri = next(graph.subjects(RDF.type, SBPMNC.startEvent))
    assert (start_uri, RDF.type, SBPMNC.catchEvent) in graph
    assert (start_uri, RDF.type, SBPMNC.event) in graph
    assert warnings == []


def test_process_gets_root_hierarchy_added():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    graph, warnings = improve_rdf(graph)

    process_uri = next(graph.subjects(RDF.type, SBPMNC.process))
    assert (process_uri, RDF.type, SBPMNC.callableElement) in graph
    assert (process_uri, RDF.type, SBPMNC.rootElement) in graph
    assert (process_uri, RDF.type, SBPMNC.baseElement) in graph
    assert warnings == []


def test_gateway_with_two_outgoing_flows_gets_no_warning():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")
    graph = to_rdf(process)

    graph, warnings = improve_rdf(graph)

    assert warnings == []


def test_gateway_with_one_outgoing_flow_gets_warning():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")
    graph = to_rdf(process)

    gateway_uri = next(graph.subjects(RDF.type, SBPMNC.exclusiveGateway))
    outgoing_flows = list(graph.subjects(SBPMNP.sourceRef, gateway_uri))
    graph.remove((outgoing_flows[0], SBPMNP.sourceRef, gateway_uri))

    graph, warnings = improve_rdf(graph)

    assert len(warnings) == 1
    assert str(gateway_uri) in warnings[0]


def test_improve_rdf_is_idempotent():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    graph, warnings_first_run = improve_rdf(graph)
    graph, warnings_second_run = improve_rdf(graph)

    assert warnings_first_run == warnings_second_run == []


def test_improve_rdf_gateway_warning_is_stable_across_runs():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")
    graph = to_rdf(process)

    gateway_uri = next(graph.subjects(RDF.type, SBPMNC.exclusiveGateway))
    outgoing_flows = list(graph.subjects(SBPMNP.sourceRef, gateway_uri))
    graph.remove((outgoing_flows[0], SBPMNP.sourceRef, gateway_uri))

    graph, warnings_first_run = improve_rdf(graph)
    graph, warnings_second_run = improve_rdf(graph)

    assert warnings_first_run == warnings_second_run
    assert len(warnings_second_run) == 1
