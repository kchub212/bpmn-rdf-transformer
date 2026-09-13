from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_file, parse_bpmn_string
from bpmn_rdf_transformer.writer.bpmn_writer import write_bpmn


def round_trip(path):
    original = parse_bpmn_file(path)
    xml_output = write_bpmn(original)
    reparsed = parse_bpmn_string(xml_output)
    return original, reparsed


def test_round_trip_minimal_process():
    original, reparsed = round_trip("tests/fixtures/valid/minimal_process.bpmn")
    assert original == reparsed


def test_round_trip_multiple_tasks():
    original, reparsed = round_trip("tests/fixtures/valid/multiple_tasks.bpmn")
    assert original == reparsed


def test_round_trip_gateway_branching():
    original, reparsed = round_trip("tests/fixtures/valid/gateway_branching.bpmn")
    assert original == reparsed


def test_output_contains_bpmn_di():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")
    xml_output = write_bpmn(process)

    assert "<bpmndi:BPMNDiagram" in xml_output
    assert xml_output.count("<bpmndi:BPMNShape") == len(process.nodes)
    assert xml_output.count("<bpmndi:BPMNEdge") == len(process.sequence_flows)
    assert "<dc:Bounds" in xml_output
    assert "<di:waypoint" in xml_output
