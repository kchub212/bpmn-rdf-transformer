from rdflib import Literal, RDF

from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_file
from bpmn_rdf_transformer.rdf.mapper import to_rdf, SBPMNC, SBPMNP


def test_output_is_valid_turtle_and_contains_expected_terms():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")
    graph = to_rdf(process)

    turtle = graph.serialize(format="turtle")

    assert "sbpmnc:startEvent" in turtle
    assert "sbpmnc:exclusiveGateway" in turtle
    assert "sbpmnc:sequenceFlow" in turtle
    assert "sbpmnp:sourceRef" in turtle
    assert "sbpmnp:targetRef" in turtle


def test_start_event_has_correct_type_and_properties():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    start_event_uri = next(graph.subjects(SBPMNP.id, Literal("StartEvent_1x4t1so")))

    assert (start_event_uri, RDF.type, SBPMNC.startEvent) in graph
    assert (start_event_uri, SBPMNP.name, Literal("Start")) in graph


def test_sequence_flow_points_at_actual_node_resources():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    flow_uri = next(graph.subjects(SBPMNP.id, Literal("Flow_195qj2q")))
    start_uri = next(graph.subjects(SBPMNP.id, Literal("StartEvent_1x4t1so")))

    assert (flow_uri, SBPMNP.sourceRef, start_uri) in graph


def test_flow_element_covers_nodes_and_flows():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")
    graph = to_rdf(process)

    process_uri = next(graph.subjects(RDF.type, SBPMNC.process))
    count = len(list(graph.objects(process_uri, SBPMNP.flowElement)))

    assert count == len(process.nodes) + len(process.sequence_flows)


def test_is_executable_is_omitted():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    assert list(graph.triples((None, SBPMNP.isExecutable, None))) == []


def test_two_conversions_produce_different_instance_uris():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph1 = to_rdf(process)
    graph2 = to_rdf(process)

    uri1 = next(graph1.subjects(RDF.type, SBPMNC.process))
    uri2 = next(graph2.subjects(RDF.type, SBPMNC.process))

    assert uri1 != uri2


def test_process_and_element_with_same_id_do_not_collide():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    process.id = "StartEvent_1x4t1so"

    graph = to_rdf(process)

    process_uri = next(graph.subjects(RDF.type, SBPMNC.process))
    start_event_uri = next(graph.subjects(RDF.type, SBPMNC.startEvent))

    assert process_uri != start_event_uri
