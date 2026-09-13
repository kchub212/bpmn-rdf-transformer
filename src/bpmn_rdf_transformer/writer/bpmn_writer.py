import xml.etree.ElementTree as ET

from bpmn_rdf_transformer.model.process import (
    StartEvent,
    EndEvent,
    Task,
    ExclusiveGateway,
    Process,
)
from bpmn_rdf_transformer.parser.validation import validate_process
from bpmn_rdf_transformer.writer.layout import compute_layout

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"

ET.register_namespace("bpmn", BPMN_NS)
ET.register_namespace("bpmndi", BPMNDI_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("di", DI_NS)


def node_size(node) -> tuple[int, int]:
    if isinstance(node, (StartEvent, EndEvent)):
        return 36, 36
    elif isinstance(node, Task):
        return 100, 80
    elif isinstance(node, ExclusiveGateway):
        return 50, 50


def write_bpmn(process: Process) -> str:
    validate_process(process)

    root = ET.Element(
        f"{{{BPMN_NS}}}definitions",
        {
            "id": "Definitions_1",
            "targetNamespace": "http://bpmn.io/schema/bpmn",
        },
    )

    process_attrib = {"id": process.id, "isExecutable": "false"}
    if process.name is not None:
        process_attrib["name"] = process.name
    process_el = ET.SubElement(root, f"{{{BPMN_NS}}}process", process_attrib)

    for node in process.nodes.values():
        if isinstance(node, StartEvent):
            tag = "startEvent"
        elif isinstance(node, EndEvent):
            tag = "endEvent"
        elif isinstance(node, Task):
            tag = "task"
        elif isinstance(node, ExclusiveGateway):
            tag = "exclusiveGateway"

        attrib = {"id": node.id}
        if node.name is not None:
            attrib["name"] = node.name
        ET.SubElement(process_el, f"{{{BPMN_NS}}}{tag}", attrib)

    for flow in process.sequence_flows:
        attrib = {
            "id": flow.id,
            "sourceRef": flow.source_ref,
            "targetRef": flow.target_ref,
        }
        if flow.name is not None:
            attrib["name"] = flow.name
        ET.SubElement(process_el, f"{{{BPMN_NS}}}sequenceFlow", attrib)

    _write_diagram(root, process)

    xml_body = ET.tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_body


def _write_diagram(root: ET.Element, process: Process) -> None:
    positions = compute_layout(process)

    diagram = ET.SubElement(root, f"{{{BPMNDI_NS}}}BPMNDiagram", {"id": "BPMNDiagram_1"})
    plane = ET.SubElement(
        diagram,
        f"{{{BPMNDI_NS}}}BPMNPlane",
        {"id": "BPMNPlane_1", "bpmnElement": process.id},
    )

    bounds_by_id = {}
    for node_id, node in process.nodes.items():
        width, height = node_size(node)
        x, y_center = positions[node_id]
        y = y_center - height // 2
        bounds_by_id[node_id] = (x, y, width, height)

        shape = ET.SubElement(
            plane,
            f"{{{BPMNDI_NS}}}BPMNShape",
            {"id": f"{node_id}_di", "bpmnElement": node_id},
        )
        ET.SubElement(
            shape,
            f"{{{DC_NS}}}Bounds",
            {"x": str(x), "y": str(y), "width": str(width), "height": str(height)},
        )

    for flow in process.sequence_flows:
        sx, sy, swidth, sheight = bounds_by_id[flow.source_ref]
        tx, ty, _, theight = bounds_by_id[flow.target_ref]

        start_point = (sx + swidth, sy + sheight // 2)
        end_point = (tx, ty + theight // 2)

        edge = ET.SubElement(
            plane,
            f"{{{BPMNDI_NS}}}BPMNEdge",
            {"id": f"{flow.id}_di", "bpmnElement": flow.id},
        )
        ET.SubElement(
            edge, f"{{{DI_NS}}}waypoint", {"x": str(start_point[0]), "y": str(start_point[1])}
        )
        ET.SubElement(
            edge, f"{{{DI_NS}}}waypoint", {"x": str(end_point[0]), "y": str(end_point[1])}
        )
