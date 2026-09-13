import xml.etree.ElementTree as ET

from bpmn_rdf_transformer.exceptions import BpmnParseError
from bpmn_rdf_transformer.model.process import (
    StartEvent,
    EndEvent,
    Task,
    ExclusiveGateway,
    SequenceFlow,
    Process,
)
from bpmn_rdf_transformer.parser.validation import validate_process


BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
NS = {"bpmn": BPMN_NS}


def parse_bpmn_string(xml_content: str):
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise BpmnParseError(f"BPMN-XML konnte nicht gelesen werden: {e}") from e

    process_element = root.find("bpmn:process", NS)

    if process_element is None:
        raise BpmnParseError("Die BPMN-Datei enthält kein <process>-Element")

    process = Process(
        id=process_element.get("id"),
        name=process_element.get("name"),
    )

    for kind in process_element:
        tag = kind.tag.split("}")[-1]

        if kind.get("id") is None:
            raise BpmnParseError(f"<{tag}>-Element hat kein id-Attribut")

        if tag == "startEvent":
            node = StartEvent(
                id=kind.get("id"),
                name=kind.get("name"),
            )

            if node.id in process.nodes:
                raise BpmnParseError(f"Doppelte ID gefunden: {node.id}")

            process.nodes[node.id] = node

        elif tag == "endEvent":
            node = EndEvent(
                id=kind.get("id"),
                name=kind.get("name"),
            )

            if node.id in process.nodes:
                raise BpmnParseError(f"Doppelte ID gefunden: {node.id}")

            process.nodes[node.id] = node

        elif tag == "task":
            node = Task(
                id=kind.get("id"),
                name=kind.get("name"),
            )

            if node.id in process.nodes:
                raise BpmnParseError(f"Doppelte ID gefunden: {node.id}")

            process.nodes[node.id] = node

        elif tag == "exclusiveGateway":
            node = ExclusiveGateway(
                id=kind.get("id"),
                name=kind.get("name"),
            )

            if node.id in process.nodes:
                raise BpmnParseError(f"Doppelte ID gefunden: {node.id}")

            process.nodes[node.id] = node

        elif tag == "sequenceFlow":
            flow = SequenceFlow(
                id=kind.get("id"),
                source_ref=kind.get("sourceRef"),
                target_ref=kind.get("targetRef"),
                name=kind.get("name"),
            )

            process.sequence_flows.append(flow)

        else:
            raise BpmnParseError(
                f"Nicht unterstütztes BPMN-Element: <{tag}>"
            )

    validate_process(process)

    return process


def parse_bpmn_file(path):
    with open(path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    return parse_bpmn_string(xml_content)