from bpmn_rdf_transformer.exceptions import BpmnValidationError
from bpmn_rdf_transformer.model.process import Process


def validate_process(process: Process) -> None:
    seen_flow_ids = set()

    for flow in process.sequence_flows:
        if flow.source_ref not in process.nodes:
            raise BpmnValidationError(
                f"Sequenzfluss '{flow.id}' verweist auf eine unbekannte sourceRef '{flow.source_ref}'"
            )

        if flow.target_ref not in process.nodes:
            raise BpmnValidationError(
                f"Sequenzfluss '{flow.id}' verweist auf eine unbekannte targetRef '{flow.target_ref}'"
            )

        if flow.id in seen_flow_ids or flow.id in process.nodes:
            raise BpmnValidationError(f"Doppelte ID gefunden: {flow.id}")

        seen_flow_ids.add(flow.id)
