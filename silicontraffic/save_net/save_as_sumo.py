# TODO: test in more scenarios

from os import PathLike
import os
import subprocess
from lxml import etree
from dataclasses import dataclass
from typing import List


@dataclass
class InternalLaneInfo:
    """内部车道信息"""
    lane_id: str
    edge_id: str
    junction_id: str
    link_index: int
    from_pos: tuple
    to_pos: tuple
    speed: float
    length: float


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

    # 生成内部车道信息
    internal_lanes_map = _generate_internal_lanes(road_net)

    _add_location_element(root, road_net)
    _add_edge_elements(root, road_net, internal_lanes_map)
    _add_junction_elements(root, road_net, internal_lanes_map)
    _add_connection_elements(root, road_net, internal_lanes_map)
    _add_tl_logic_elements(root, road_net)

    tree = etree.ElementTree(root)
    tree.write(filename, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    
    # 调用 netconvert 处理路网文件
    _run_netconvert(filename)


def _generate_internal_lanes(road_net) -> dict:
    """
    为每个连接生成内部车道信息。
    
    Returns:
        dict: {junction_id: {link_index: InternalLaneInfo}}
    """
    internal_lanes_map = {}
    
    for junction in road_net.junctions:
        tl = road_net.get_traffic_light(junction.id)
        if tl:
            # 对于有交通灯的交叉口，按照 controlled_links 的顺序生成内部车道
            junction_lanes = {}
            for link_index, link in enumerate(tl.controlled_links):
                internal_lane_info = _create_internal_lane_info(link, junction, link_index)
                if internal_lane_info:
                    junction_lanes[link_index] = internal_lane_info
            if junction_lanes:
                internal_lanes_map[junction.id] = junction_lanes
        else:
            # 对于没有交通灯的交叉口，按照 lane_links 的顺序生成内部车道
            junction_lanes = {}
            for link_index, link in enumerate(junction.lane_links):
                internal_lane_info = _create_internal_lane_info(link, junction, link_index)
                if internal_lane_info:
                    junction_lanes[link_index] = internal_lane_info
            if junction_lanes:
                internal_lanes_map[junction.id] = junction_lanes
    
    return internal_lanes_map


def _create_internal_lane_info(link, junction, link_index: int):
    """创建单个内部车道信息"""
    from_lane = link.from_lane
    to_lane = link.to_lane
    
    # 获取交叉口位置
    junction_pos = _get_position(junction.position)
    
    # 计算内部车道的起点和终点
    # 起点是从进入边车道接近交叉口的位置
    # 终点是到离开边车道离开交叉口的位置
    
    from_pos = junction_pos
    to_pos = junction_pos
    
    # 计算进入边和离开边的方向
    from_dir = None
    to_dir = None
    
    if from_lane and from_lane.parent_edge:
        from_edge = from_lane.parent_edge
        if from_edge.from_junction and from_edge.to_junction:
            from_junc_pos = _get_position(from_edge.from_junction.position)
            to_junc_pos = _get_position(from_edge.to_junction.position)
            dx = to_junc_pos[0] - from_junc_pos[0]
            dy = to_junc_pos[1] - from_junc_pos[1]
            length = (dx ** 2 + dy ** 2) ** 0.5
            if length > 0.001:
                # 进入边的方向向量（指向交叉口）
                from_dir = (dx / length, dy / length)
                # 起点位置：交叉口位置向进入边方向偏移一小段距离
                from_pos = (junction_pos[0] - from_dir[0] * 5.0, junction_pos[1] - from_dir[1] * 5.0)
    
    if to_lane and to_lane.parent_edge:
        to_edge = to_lane.parent_edge
        if to_edge.from_junction and to_edge.to_junction:
            from_junc_pos = _get_position(to_edge.from_junction.position)
            to_junc_pos = _get_position(to_edge.to_junction.position)
            dx = to_junc_pos[0] - from_junc_pos[0]
            dy = to_junc_pos[1] - from_junc_pos[1]
            length = (dx ** 2 + dy ** 2) ** 0.5
            if length > 0.001:
                # 离开边的方向向量（离开交叉口）
                to_dir = (dx / length, dy / length)
                # 终点位置：交叉口位置向离开边方向偏移一小段距离
                to_pos = (junction_pos[0] + to_dir[0] * 5.0, junction_pos[1] + to_dir[1] * 5.0)
    
    # 生成内部边和车道 ID
    edge_id = f":{junction.id}_{link_index}"
    lane_id = f":{junction.id}_{link_index}_0"
    
    # 计算内部车道长度
    dx = to_pos[0] - from_pos[0]
    dy = to_pos[1] - from_pos[1]
    length = (dx ** 2 + dy ** 2) ** 0.5
    if length < 1.0:
        length = 10.0  # 最小长度
    
    # 获取速度限制
    speed = 13.89
    if from_lane and from_lane.speed_limit != float('inf'):
        speed = from_lane.speed_limit
    
    return InternalLaneInfo(
        lane_id=lane_id,
        edge_id=edge_id,
        junction_id=junction.id,
        link_index=link_index,
        from_pos=from_pos,
        to_pos=to_pos,
        speed=speed,
        length=length
    )


def _get_position(position):
    """Get position as tuple, handling both dict and tuple formats."""
    if isinstance(position, dict):
        return (position['x'], position['y'])
    return position


def _generate_octagon_shape(center_x: float, center_y: float, radius: float = 10.0) -> str:
    """
    生成正八边形的 shape 字符串。
    
    :param center_x: 中心点 x 坐标
    :param center_y: 中心点 y 坐标
    :param radius: 外接圆半径（从中心到顶点的距离）
    :return: 八边形的 shape 字符串
    """
    import math
    
    points = []
    # 正八边形有8个顶点，每个顶点间隔45度（π/4弧度）
    for i in range(8):
        angle = 2 * math.pi * i / 8 - math.pi / 4  # 从45度开始，使边与坐标轴对齐
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        points.append(f"{x:.2f},{y:.2f}")
    
    return " ".join(points)


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


def _add_edge_elements(root: etree.Element, road_net, internal_lanes_map: dict):
    """Add edge elements to the net."""
    # 首先添加内部边
    for junction_id, junction_lanes in internal_lanes_map.items():
        for link_index, lane_info in junction_lanes.items():
            _add_internal_edge_element(root, lane_info)
    
    # 然后添加普通边
    for edge in road_net.edges:
        if not edge.id.startswith(":"):
            _add_edge_element(root, edge, is_internal=False)


def _add_internal_edge_element(root: etree.Element, lane_info: InternalLaneInfo):
    """添加内部边元素"""
    edge_elem = etree.SubElement(root, "edge")
    edge_elem.set("id", lane_info.edge_id)
    edge_elem.set("function", "internal")
    
    # 添加内部车道
    lane_elem = etree.SubElement(edge_elem, "lane")
    lane_elem.set("id", lane_info.lane_id)
    lane_elem.set("index", "0")
    lane_elem.set("speed", f"{lane_info.speed:.2f}")
    lane_elem.set("length", f"{lane_info.length:.2f}")
    
    # 计算 shape
    shape_str = f"{lane_info.from_pos[0]:.2f},{lane_info.from_pos[1]:.2f} {lane_info.to_pos[0]:.2f},{lane_info.to_pos[1]:.2f}"
    lane_elem.set("shape", shape_str)


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


def _add_junction_elements(root: etree.Element, road_net, internal_lanes_map: dict):
    """Add junction elements to the net."""
    for junction in road_net.junctions:
        _add_junction_element(root, junction, road_net, internal_lanes_map)


def _add_junction_element(root: etree.Element, junction, road_net, internal_lanes_map: dict):
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
    
    # 从 internal_lanes_map 获取内部车道
    if junction.id in internal_lanes_map:
        for link_index in sorted(internal_lanes_map[junction.id].keys()):
            lane_info = internal_lanes_map[junction.id][link_index]
            int_lanes.append(lane_info.lane_id)
    
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
        # 生成正八边形的 shape
        shape_str = _generate_octagon_shape(pos[0], pos[1])
    junction_elem.set("shape", shape_str)


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


def _add_connection_elements(root: etree.Element, road_net, internal_lanes_map: dict):
    """Add connection elements to the net."""
    for junction in road_net.junctions:
        tl = road_net.get_traffic_light(junction.id)
        if tl:
            # 对于有交通灯的交叉口，按照 controlled_links 的顺序添加连接
            for link_index, link in enumerate(tl.controlled_links):
                _add_connection_element(root, link, junction, road_net, internal_lanes_map, link_index)
        else:
            # 对于没有交通灯的交叉口，按照 lane_links 的顺序添加连接
            for link_index, link in enumerate(junction.lane_links):
                _add_connection_element(root, link, junction, road_net, internal_lanes_map, link_index)


def _add_connection_element(root: etree.Element, link, junction, road_net, internal_lanes_map: dict, link_index: int):
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
    
    # 设置 via 属性（内部车道）
    if junction.id in internal_lanes_map and link_index in internal_lanes_map[junction.id]:
        lane_info = internal_lanes_map[junction.id][link_index]
        connection.set("via", lane_info.lane_id)
    
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


def _run_netconvert(input_file: PathLike):
    """
    调用 SUMO 的 netconvert 工具处理路网文件，使其具有可用性。
    
    Args:
        input_file: 输入的 .net.xml 文件路径
    """
    input_file = str(input_file)
    
    # 生成输出文件名（在原文件名后添加 _processed）
    if input_file.endswith('.net.xml'):
        output_file = input_file[:-8] + '_processed.net.xml'
    else:
        output_file = input_file + '_processed.net.xml'
    
    # 构建 netconvert 命令
    command = ['netconvert', '-s', input_file, '--output-file', output_file]
    
    try:
        # 执行命令
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"netconvert 成功！处理后的文件: {output_file}")
            # 将处理后的文件覆盖原文件
            os.replace(output_file, input_file)
            print(f"已用处理后的文件覆盖原文件: {input_file}")
        else:
            print(f"netconvert 失败！错误信息: {result.stderr}")
            print(f"请手动运行以下命令处理路网文件:")
            print(f"  netconvert -s {input_file} --output-file={output_file}")
    except FileNotFoundError:
        print("netconvert 命令未找到！请确保 SUMO 已正确安装并添加到 PATH 环境变量中。")
        print(f"请手动运行以下命令处理路网文件:")
        print(f"  netconvert -s {input_file} --output-file={output_file}")
    except Exception as e:
        print(f"调用 netconvert 时发生错误: {e}")
        print(f"请手动运行以下命令处理路网文件:")
        print(f"  netconvert -s {input_file} --output-file={output_file}")