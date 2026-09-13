import pytest
from rdflib import RDF, Literal, Namespace

from bpmn_rdf_transformer.exceptions import RdfValidationError
from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_file
from bpmn_rdf_transformer.rdf.mapper import SBPMNC, SBPMNP, to_rdf
from bpmn_rdf_transformer.rdf.validation import validate_rdf


def test_valid_graph_passes():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")
    graph = to_rdf(process)

    validate_rdf(graph)


def test_dangling_reference_raises():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    flow_uri = next(graph.subjects(RDF.type, SBPMNC.sequenceFlow))
    ghost = Namespace("http://example.org/")["ghost"]
    graph.set((flow_uri, SBPMNP.sourceRef, ghost))

    with pytest.raises(RdfValidationError):
        validate_rdf(graph)


def test_duplicate_id_within_same_process_raises():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    start_uri = next(graph.subjects(RDF.type, SBPMNC.startEvent))
    end_uri = next(graph.subjects(RDF.type, SBPMNC.endEvent))
    end_id = next(graph.objects(end_uri, SBPMNP.id))

    graph.set((start_uri, SBPMNP.id, end_id))

    with pytest.raises(RdfValidationError):
        validate_rdf(graph)


def test_process_id_equal_to_element_id_does_not_raise():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    process.id = "StartEvent_1x4t1so"
    graph = to_rdf(process)

    validate_rdf(graph)


def test_same_id_in_two_different_processes_does_not_raise():
    process_a = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    process_b = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")

    combined = to_rdf(process_a) + to_rdf(process_b)

    validate_rdf(combined)


def test_missing_id_raises():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    start_uri = next(graph.subjects(RDF.type, SBPMNC.startEvent))
    graph.remove((start_uri, SBPMNP.id, None))

    with pytest.raises(RdfValidationError):
        validate_rdf(graph)


def test_multiple_ids_on_same_element_raises():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    start_uri = next(graph.subjects(RDF.type, SBPMNC.startEvent))
    graph.add((start_uri, SBPMNP.id, Literal("some_other_id")))

    with pytest.raises(RdfValidationError):
        validate_rdf(graph)


def test_source_ref_pointing_at_non_flow_node_raises():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    flow_uri = next(graph.subjects(RDF.type, SBPMNC.sequenceFlow))
    graph.set((flow_uri, SBPMNP.sourceRef, flow_uri))

    with pytest.raises(RdfValidationError):
        validate_rdf(graph)
