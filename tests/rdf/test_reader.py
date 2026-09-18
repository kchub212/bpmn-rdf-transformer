import pytest
from rdflib import RDF, Graph, Namespace

from bpmn_rdf_transformer.exceptions import RdfValidationError
from bpmn_rdf_transformer.model.process import ExclusiveGateway
from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_file
from bpmn_rdf_transformer.rdf.improvement import improve_rdf
from bpmn_rdf_transformer.rdf.mapper import SBPMNC, SBPMNP, to_rdf
from bpmn_rdf_transformer.rdf.reader import from_rdf


def test_process_id_and_name_are_restored():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    rebuilt = from_rdf(graph)

    assert rebuilt.id == process.id
    assert rebuilt.name == process.name


def test_nodes_are_restored_with_correct_types_ids_and_names():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")
    graph = to_rdf(process)

    rebuilt = from_rdf(graph)

    assert rebuilt.nodes == process.nodes


def test_sequence_flows_are_restored():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")
    graph = to_rdf(process)

    rebuilt = from_rdf(graph)

    assert set(rebuilt.sequence_flows) == set(process.sequence_flows)


def test_concrete_type_still_detected_after_enrichment():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")
    graph = to_rdf(process)
    graph, _ = improve_rdf(graph)

    rebuilt = from_rdf(graph)

    assert rebuilt.nodes == process.nodes
    gateway = next(n for n in rebuilt.nodes.values() if isinstance(n, ExclusiveGateway))
    assert isinstance(gateway, ExclusiveGateway)


def test_dangling_reference_raises():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    flow_uri = next(graph.subjects(RDF.type, SBPMNC.sequenceFlow))
    ghost = Namespace("http://example.org/")["ghost"]
    graph.set((flow_uri, SBPMNP.sourceRef, ghost))

    with pytest.raises(RdfValidationError):
        from_rdf(graph)


def test_no_process_in_graph_raises():
    with pytest.raises(RdfValidationError):
        from_rdf(Graph())


def test_multiple_processes_in_graph_raises():
    process_a = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    process_b = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")

    combined = to_rdf(process_a) + to_rdf(process_b)

    with pytest.raises(RdfValidationError):
        from_rdf(combined)
