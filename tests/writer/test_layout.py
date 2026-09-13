from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_file
from bpmn_rdf_transformer.writer.layout import compute_layout


def test_levels_increase_along_a_chain():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    positions = compute_layout(process)

    start_x, _ = positions["StartEvent_1x4t1so"]
    task_x, _ = positions["Activity_1nn9wmy"]
    end_x, _ = positions["Event_1fajtpa"]

    assert start_x < task_x < end_x


def test_branches_get_different_rows():
    process = parse_bpmn_file("tests/fixtures/valid/gateway_branching.bpmn")
    positions = compute_layout(process)

    task_a_x, task_a_y = positions["Task_A"]
    task_b_x, task_b_y = positions["Task_B"]

    assert task_a_x == task_b_x
    assert task_a_y != task_b_y
