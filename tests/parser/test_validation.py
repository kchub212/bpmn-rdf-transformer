import pytest

from bpmn_rdf_transformer.exceptions import BpmnValidationError
from bpmn_rdf_transformer.model.process import Process, StartEvent, Task, EndEvent, SequenceFlow
from bpmn_rdf_transformer.parser.validation import validate_process


def build_valid_process():
    process = Process(id="Process_1")
    process.nodes["Start_1"] = StartEvent(id="Start_1")
    process.nodes["Task_1"] = Task(id="Task_1")
    process.nodes["End_1"] = EndEvent(id="End_1")
    process.sequence_flows.append(SequenceFlow(id="Flow_1", source_ref="Start_1", target_ref="Task_1"))
    process.sequence_flows.append(SequenceFlow(id="Flow_2", source_ref="Task_1", target_ref="End_1"))
    return process


def test_valid_process_passes():
    process = build_valid_process()
    validate_process(process)


def test_dangling_source_ref_raises():
    process = build_valid_process()
    process.sequence_flows[0] = SequenceFlow(id="Flow_1", source_ref="NotExist", target_ref="Task_1")

    with pytest.raises(BpmnValidationError):
        validate_process(process)


def test_dangling_target_ref_raises():
    process = build_valid_process()
    process.sequence_flows[0] = SequenceFlow(id="Flow_1", source_ref="Start_1", target_ref="NotExist")

    with pytest.raises(BpmnValidationError):
        validate_process(process)


def test_duplicate_flow_vs_flow_id_raises():
    process = build_valid_process()
    process.sequence_flows[1] = SequenceFlow(id="Flow_1", source_ref="Task_1", target_ref="End_1")

    with pytest.raises(BpmnValidationError):
        validate_process(process)


def test_duplicate_flow_vs_node_id_raises():
    process = build_valid_process()
    process.sequence_flows[0] = SequenceFlow(id="Start_1", source_ref="Start_1", target_ref="Task_1")

    with pytest.raises(BpmnValidationError):
        validate_process(process)
