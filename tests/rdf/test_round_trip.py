from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_file, parse_bpmn_string
from bpmn_rdf_transformer.rdf.mapper import to_rdf
from bpmn_rdf_transformer.rdf.reader import from_rdf
from bpmn_rdf_transformer.writer.bpmn_writer import write_bpmn


def _assert_semantically_equal(original, reparsed):
    assert reparsed.id == original.id
    assert reparsed.name == original.name
    assert reparsed.nodes == original.nodes
    assert set(reparsed.sequence_flows) == set(original.sequence_flows)


def test_full_round_trip_minimal_process():
    original = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")

    graph = to_rdf(original)
    rebuilt = from_rdf(graph)
    reparsed = parse_bpmn_string(write_bpmn(rebuilt))

    _assert_semantically_equal(original, reparsed)


def test_full_round_trip_multiple_tasks():
    original = parse_bpmn_file("tests/fixtures/valid/multiple_tasks.bpmn")

    graph = to_rdf(original)
    rebuilt = from_rdf(graph)
    reparsed = parse_bpmn_string(write_bpmn(rebuilt))

    _assert_semantically_equal(original, reparsed)


def test_full_round_trip_gateway_branching():
    original = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")

    graph = to_rdf(original)
    rebuilt = from_rdf(graph)
    reparsed = parse_bpmn_string(write_bpmn(rebuilt))

    _assert_semantically_equal(original, reparsed)
