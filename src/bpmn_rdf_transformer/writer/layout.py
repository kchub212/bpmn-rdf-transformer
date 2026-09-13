from bpmn_rdf_transformer.model.process import Process

LEVEL_SPACING = 150
ROW_SPACING = 120
START_X = 160
START_Y = 120


def compute_layout(process: Process) -> dict[str, tuple[int, int]]:
    incoming_count = {node_id: 0 for node_id in process.nodes}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in process.nodes}

    for flow in process.sequence_flows:
        outgoing[flow.source_ref].append(flow.target_ref)
        incoming_count[flow.target_ref] += 1

    level: dict[str, int] = {}
    queue = [node_id for node_id, count in incoming_count.items() if count == 0]
    for node_id in queue:
        level[node_id] = 0

    remaining = dict(incoming_count)
    while queue:
        node_id = queue.pop(0)
        for target_id in outgoing[node_id]:
            level[target_id] = max(level.get(target_id, 0), level[node_id] + 1)
            remaining[target_id] -= 1
            if remaining[target_id] == 0:
                queue.append(target_id)

    for node_id in process.nodes:
        if node_id not in level:
            level[node_id] = 0

    nodes_by_level: dict[int, list[str]] = {}
    for node_id in process.nodes:
        nodes_by_level.setdefault(level[node_id], []).append(node_id)

    positions: dict[str, tuple[int, int]] = {}
    for lvl, node_ids in nodes_by_level.items():
        for row, node_id in enumerate(node_ids):
            x = START_X + lvl * LEVEL_SPACING
            y = START_Y + row * ROW_SPACING
            positions[node_id] = (x, y)

    return positions
