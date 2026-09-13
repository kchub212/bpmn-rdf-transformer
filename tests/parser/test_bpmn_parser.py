from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_file
from bpmn_rdf_transformer.exceptions import BpmnParseError, BpmnValidationError
import pytest

def test_parse_minimal_process():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")

    assert  len(process.nodes) == 3
    assert len(process.sequence_flows) == 2

def test_parse_multiple_tasks_process():
    process = parse_bpmn_file("tests/fixtures/valid/multiple_tasks.bpmn")

    assert len(process.nodes) == 4
    assert len(process.sequence_flows) == 3

def test_parse_unsupported_bpmn_element():
    with pytest.raises(BpmnParseError):
        parse_bpmn_file("tests/fixtures/invalid/unsupported_element.bpmn")


def test_parse_missing_id_raises():
    with pytest.raises(BpmnParseError):
        parse_bpmn_file("tests/fixtures/invalid/missing_id.bpmn")


def test_parse_malformed_xml_raises():
    with pytest.raises(BpmnParseError):
        parse_bpmn_file("tests/fixtures/invalid/malformed.bpmn")


def test_parse_duplicate_node_id_raises():
    with pytest.raises(BpmnParseError):
        parse_bpmn_file("tests/fixtures/invalid/duplicate_id.bpmn")


def test_parse_dangling_source_ref_raises():
    with pytest.raises(BpmnValidationError):
        parse_bpmn_file("tests/fixtures/invalid/bad_source_ref.bpmn")


def test_parse_duplicate_flow_id_raises():
    with pytest.raises(BpmnValidationError):
        parse_bpmn_file("tests/fixtures/invalid/duplicate_flow_id.bpmn")


def test_parse_gateway_branching():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")

    assert len(process.nodes) == 6
    assert len(process.sequence_flows) == 5

