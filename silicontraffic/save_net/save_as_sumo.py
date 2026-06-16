from os import PathLike
from lxml import etree


def save_as_sumo(road_net, filename: PathLike):
    """
    Save the road net to disk in the SUMO format.

    Args:
        road_net: The road net to save.
        filename: The path to save the file to.
    """
    ns_map = {
        None: "http://sumo.dlr.de/xsd/net_file.xsd",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance"
    }
    root = etree.Element("net", nsmap=ns_map)
    root.set("version", "1.16")
    root.set("junctionCornerDetail", "5")
    root.set("limitTurnSpeed", "5.50")
    root.set("{%s}noNamespaceSchemaLocation" % ns_map["xsi"], "http://sumo.dlr.de/xsd/net_file.xsd")

    _add_location_element(root, road_net)
    _add_edge_elements(root, road_net)
    _add_junction_elements(root, road_net)
    _add_connection_elements(root, road_net)
    _add_tl_logic_elements(root, road_net)

    tree = etree.ElementTree(root)
    tree.write(filename, pretty_print=True, xml_declaration=True, encoding="UTF-8")


def _get_position(position):
    """Get position as tuple, handling both dict and tuple formats."""
    if isinstance(position, dict):
        return (position['x'], position['y'])
    return position


def _add_location_element(root: etree.Element, road_net):
    """Add location element to the net."""
    x_coords = []
    y_coords = []

    for junction in road_net.junctions:
        pos = _get_position(junction.position)
        x_coords.append(pos[0])
        y_coords.append(pos[1])
    
    for lane in road_net.lanes:
        for point in lane.shape:
            if isinstance(point, dict):
                x_coords.append(point['x'])
                y_coords.append(point['y'])
            else:
                x_coords.append(point[0])
                y_coords.append(point[1])

    if not x_coords or not y_coords:
        min_x, max_x, min_y, max_y = -1000, 1000, -1000, 1000
    else:
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
    
    padding = 10.0
    conv_boundary = f"{min_x - padding:.2f},{min_y - padding:.2f},{max_x + padding:.2f},{max_y + padding:.2f}"
    orig_boundary = "-10000000000.00,-10000000000.00,10000000000.00,10000000000.00"

    location = etree.SubElement(root, "location")
    location.set("netOffset", "0.00,0.00")
    location.set("convBoundary", conv_boundary)
    location.set("origBoundary", orig_boundary)
    location.set("projParameter", "!")


def _add_edge_elements(root: etree.Element, road_net):
    """Add edge elements to the net."""
    internal_edges = []
    regular_edges = []

    for edge in road_net.edges:
        if edge.id.startswith(":"):
            internal_edges.append(edge)
        else:
            regular_edges.append(edge)

    for edge in internal_edges:
        _add_edge_element(root, edge, is_internal=True)
    
    for edge in regular_edges:
        _add_edge_element(root, edge, is_internal=False)


def _add_edge_element(root: etree.Element, edge, is_internal: bool):
    """Add a single edge element."""
    edge_elem = etree.SubElement(root, "edge")
    edge_elem.set("id", edge.id)
    
    if is_internal:
        edge_elem.set("function", "internal")
    else:
        edge_elem.set("from", edge.from_junction.id)
        edge_elem.set("to", edge.to_junction.id)
        edge_elem.set("priority", "-1")

    for lane in edge.lanes:
        _add_lane_element(edge_elem, lane, edge)


def _add_lane_element(edge_elem: etree.Element, lane, edge):
    """Add a lane element to an edge."""
    lane_elem = etree.SubElement(edge_elem, "lane")
    lane_elem.set("id", lane.id)
    
    # 反转车道索引：CityFlow 从右到左编号，SUMO 从左到右编号
    num_lanes = len(edge.lanes)
    reversed_index = num_lanes - 1 - lane.index
    lane_elem.set("index", str(reversed_index))
    
    if lane.speed_limit != float('inf'):
        lane_elem.set("speed", f"{lane.speed_limit:.2f}")
    else:
        lane_elem.set("speed", "13.89")
    
    lane_elem.set("length", f"{lane.length:.2f}")
    
    if lane.shape:
        shape_points = []
        for point in lane.shape:
            if isinstance(point, dict):
                shape_points.append(f"{point['x']:.2f},{point['y']:.2f}")
            else:
                shape_points.append(f"{point[0]:.2f},{point[1]:.2f}")
        shape_str = " ".join(shape_points)
        lane_elem.set("shape", shape_str)
    else:
        # 如果没有 shape，根据边的方向和车道宽度计算车道位置
        from_pos = _get_position(edge.from_junction.position)
        to_pos = _get_position(edge.to_junction.position)
        
        # 使用反转后的索引计算车道位置，确保车道顺序正确
        shape_str = _calculate_lane_shape(from_pos, to_pos, reversed_index, lane.width, num_lanes)
        lane_elem.set("shape", shape_str)
    
    if lane.allowed:
        lane_elem.set("allow", " ".join(lane.allowed))


def _calculate_lane_shape(from_pos, to_pos, lane_index, lane_width, num_lanes):
    """
    计算车道的 shape，考虑车道宽度和车道索引。
    
    :param from_pos: 边的起点位置 (x, y)
    :param to_pos: 边的终点位置 (x, y)
    :param lane_index: 车道索引（从0开始）
    :param lane_width: 车道宽度
    :param num_lanes: 边的车道总数
    :return: 车道的 shape 字符串
    """
    dx = to_pos[0] - from_pos[0]
    dy = to_pos[1] - from_pos[1]
    
    # 计算边的长度
    length = (dx ** 2 + dy ** 2) ** 0.5
    
    if length < 0.001:
        # 如果边太短，直接返回起点位置
        return f"{from_pos[0]:.2f},{from_pos[1]:.2f} {to_pos[0]:.2f},{to_pos[1]:.2f}"
    
    # 计算单位方向向量
    ux = dx / length
    uy = dy / length
    
    # 计算垂直于边方向的单位法向量（向左为正）
    nx = -uy
    ny = ux
    
    # 计算车道的横向偏移
    # 车道从右向左排列（相对于行驶方向），中间车道偏移为0
    # 总偏移量 = (车道索引 - (总车道数-1)/2) * 车道宽度
    offset = (lane_index - (num_lanes - 1) / 2) * lane_width
    
    # 应用偏移到起点和终点
    from_x = from_pos[0] + nx * offset
    from_y = from_pos[1] + ny * offset
    to_x = to_pos[0] + nx * offset
    to_y = to_pos[1] + ny * offset
    
    return f"{from_x:.2f},{from_y:.2f} {to_x:.2f},{to_y:.2f}"


def _add_junction_elements(root: etree.Element, road_net):
    """Add junction elements to the net."""
    for junction in road_net.junctions:
        _add_junction_element(root, junction, road_net)


def _add_junction_element(root: etree.Element, junction, road_net):
    """Add a single junction element."""
    junction_elem = etree.SubElement(root, "junction")
    junction_elem.set("id", junction.id)
    
    junction_type = _determine_junction_type(junction, road_net)
    junction_elem.set("type", junction_type)
    
    pos = _get_position(junction.position)
    junction_elem.set("x", f"{pos[0]:.2f}")
    junction_elem.set("y", f"{pos[1]:.2f}")

    inc_lanes = []
    int_lanes = []
    
    for edge in junction.in_coming_edges:
        for lane in edge.lanes:
            inc_lanes.append(lane.id)
    
    for link in junction.lane_links:
        if link.link_lane and link.link_lane.id not in int_lanes:
            int_lanes.append(link.link_lane.id)
    
    junction_elem.set("incLanes", " ".join(inc_lanes))
    junction_elem.set("intLanes", " ".join(int_lanes))

    if junction.shape:
        shape_points = []
        for point in junction.shape:
            if isinstance(point, dict):
                shape_points.append(f"{point['x']:.2f},{point['y']:.2f}")
            else:
                shape_points.append(f"{point[0]:.2f},{point[1]:.2f}")
        shape_str = " ".join(shape_points)
    else:
        pos = _get_position(junction.position)
        shape_str = f"{pos[0]:.2f},{pos[1]:.2f}"
    junction_elem.set("shape", shape_str)

    _add_request_elements(junction_elem, junction, road_net)


def _determine_junction_type(junction, road_net) -> str:
    """Determine the junction type."""
    tl = road_net.get_traffic_light(junction.id)
    if tl:
        return "traffic_light"
    
    in_count = len(junction.in_coming_edges)
    out_count = len(junction.out_going_edges)
    
    if in_count == 0 or out_count == 0:
        return "dead_end"
    
    return "priority"


def _add_request_elements(junction_elem: etree.Element, junction, road_net):
    """Add request elements to a junction."""
    inc_lanes = []
    for edge in junction.in_coming_edges:
        for lane in edge.lanes:
            inc_lanes.append(lane.id)
    
    if not inc_lanes:
        return
    
    tl = road_net.get_traffic_light(junction.id)
    if tl:
        _add_traffic_light_requests(junction_elem, junction, inc_lanes, tl)
    else:
        _add_default_requests(junction_elem, inc_lanes)


def _add_traffic_light_requests(junction_elem: etree.Element, junction, inc_lanes: list[str], tl):
    """Add request elements for traffic light junction."""
    lane_to_index = {lane: idx for idx, lane in enumerate(inc_lanes)}
    
    for link in tl.controlled_links:
        if link.from_lane.id in lane_to_index:
            index = lane_to_index[link.from_lane.id]
            request = etree.SubElement(junction_elem, "request")
            request.set("index", str(index))
            request.set("response", "0" * len(inc_lanes))
            request.set("foes", "0" * len(inc_lanes))
            request.set("cont", "0")


def _add_default_requests(junction_elem: etree.Element, inc_lanes: list[str]):
    """Add default request elements for non-traffic-light junction."""
    for i in range(len(inc_lanes)):
        request = etree.SubElement(junction_elem, "request")
        request.set("index", str(i))
        request.set("response", "0" * len(inc_lanes))
        request.set("foes", "0" * len(inc_lanes))
        request.set("cont", "0")


def _add_connection_elements(root: etree.Element, road_net):
    """Add connection elements to the net."""
    for junction in road_net.junctions:
        tl = road_net.get_traffic_light(junction.id)
        if tl:
            # 对于有交通灯的交叉口，按照 controlled_links 的顺序添加连接
            for link in tl.controlled_links:
                _add_connection_element(root, link, junction, road_net)
        else:
            # 对于没有交通灯的交叉口，按照 lane_links 的顺序添加连接
            for link in junction.lane_links:
                _add_connection_element(root, link, junction, road_net)


def _add_connection_element(root: etree.Element, link, junction, road_net):
    """Add a single connection element."""
    connection = etree.SubElement(root, "connection")
    
    connection.set("from", link.from_lane.parent_edge.id)
    connection.set("to", link.to_lane.parent_edge.id)
    
    # 反转车道索引：CityFlow 从右到左编号，SUMO 从左到右编号
    from_num_lanes = len(link.from_lane.parent_edge.lanes)
    to_num_lanes = len(link.to_lane.parent_edge.lanes)
    
    from_lane_index = from_num_lanes - 1 - link.from_lane.index
    to_lane_index = to_num_lanes - 1 - link.to_lane.index
    
    connection.set("fromLane", str(from_lane_index))
    connection.set("toLane", str(to_lane_index))
    
    if link.link_lane:
        connection.set("via", link.link_lane.id)
    
    direction = _determine_direction(link, junction)
    connection.set("dir", direction)
    
    tl = road_net.get_traffic_light(junction.id)
    if tl:
        _add_traffic_light_connection_attrs(connection, link, tl)
    else:
        connection.set("state", "M")


def _determine_direction(link, junction) -> str:
    """Determine the direction of a connection."""
    from_edge = link.from_lane.parent_edge
    to_edge = link.to_lane.parent_edge
    
    if from_edge.to_junction == junction and to_edge.from_junction == junction:
        from_dir = _get_edge_direction(from_edge)
        to_dir = _get_edge_direction(to_edge)
        
        if from_dir == to_dir:
            return "s"
        elif (from_dir, to_dir) in [("N", "E"), ("E", "S"), ("S", "W"), ("W", "N")]:
            return "r"
        else:
            return "l"
    
    return "s"


def _get_edge_direction(edge) -> str:
    """Determine the direction of an edge based on junction positions."""
    from_pos = _get_position(edge.from_junction.position)
    to_pos = _get_position(edge.to_junction.position)
    dx = to_pos[0] - from_pos[0]
    dy = to_pos[1] - from_pos[1]
    
    if abs(dy) > abs(dx):
        return "N" if dy > 0 else "S"
    else:
        return "E" if dx > 0 else "W"


def _add_traffic_light_connection_attrs(connection: etree.Element, link, tl):
    """Add traffic light attributes to a connection."""
    connection.set("tl", tl.id)
    
    # 找到这个连接在 controlled_links 中的索引
    link_index = None
    for i, controlled_link in enumerate(tl.controlled_links):
        if controlled_link == link:
            link_index = i
            break
    
    if link_index is not None:
        connection.set("linkIndex", str(link_index))
    
    state = _determine_connection_state(link, tl)
    connection.set("state", state)


def _determine_connection_state(link, tl) -> str:
    """Determine the state of a connection based on traffic light."""
    for phase in tl.phases:
        if link not in phase.available_links and link in tl.controlled_links:
            return "O"
    
    return "o"


def _add_tl_logic_elements(root: etree.Element, road_net):
    """Add traffic light logic elements to the net."""
    for tl in road_net.traffic_lights:
        _add_tl_logic_element(root, tl)


def _add_tl_logic_element(root: etree.Element, tl):
    """Add a single traffic light logic element."""
    tl_logic = etree.SubElement(root, "tlLogic")
    tl_logic.set("id", tl.id)
    tl_logic.set("type", "static")
    tl_logic.set("programID", "0")
    tl_logic.set("offset", "0")
    
    for phase in tl.phases:
        _add_phase_element(tl_logic, phase, tl)


def _add_phase_element(tl_logic: etree.Element, phase, tl):
    """Add a phase element to a traffic light logic."""
    phase_elem = etree.SubElement(tl_logic, "phase")
    phase_elem.set("duration", str(int(phase.duration)))
    
    state_str = _build_phase_state(phase, tl)
    phase_elem.set("state", state_str)


def _build_phase_state(phase, tl) -> str:
    """Build the state string for a traffic light phase."""
    state = []
    
    for link in tl.controlled_links:
        if link in phase.available_links:
            state.append("g")
        elif link in tl.uncontrolled_links:
            state.append("G")
        else:
            state.append("r")
    
    return "".join(state)