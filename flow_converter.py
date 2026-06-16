import json
from lxml import etree

def convert_cityflow_flow_to_sumo(cityflow_flow_path: str, road_net, output_path: str):
    """
    将 CityFlow 车流文件转换为 SUMO 的 .rou.xml 文件
    
    Args:
        cityflow_flow_path: CityFlow 车流文件路径
        road_net: RoadNet 对象，用于获取道路信息
        output_path: 输出的 SUMO .rou.xml 文件路径
    """
    # 读取 CityFlow 车流文件
    with open(cityflow_flow_path, 'r') as f:
        flow_data = json.load(f)
    
    # 创建 XML 根元素
    root = etree.Element("routes")
    
    # 创建车辆类型（从第一个车辆定义中提取参数）
    if flow_data:
        first_vehicle = flow_data[0]['vehicle']
        vtype = etree.SubElement(root, "vType")
        vtype.set("id", "car")
        vtype.set("length", str(first_vehicle['length']))
        vtype.set("width", str(first_vehicle['width']))
        vtype.set("accel", str(first_vehicle['usualPosAcc']))
        vtype.set("decel", str(first_vehicle['usualNegAcc']))
        vtype.set("maxSpeed", str(first_vehicle['maxSpeed']))
        vtype.set("minGap", str(first_vehicle['minGap']))
        vtype.set("headwayTime", str(first_vehicle['headwayTime']))
    
    # 按路线分组车流
    route_flows = {}
    for flow_item in flow_data:
        route_key = tuple(flow_item['route'])
        if route_key not in route_flows:
            route_flows[route_key] = {
                'start_times': [],
                'end_times': [],
                'intervals': []
            }
        route_flows[route_key]['start_times'].append(flow_item['startTime'])
        route_flows[route_key]['end_times'].append(flow_item['endTime'])
        route_flows[route_key]['intervals'].append(flow_item['interval'])
    
    # 创建 flow 元素
    flow_id = 0
    for route_key, data in route_flows.items():
        route = list(route_key)
        if len(route) < 2:
            continue
        
        # 获取起始边和终点边
        from_edge = route[0]
        to_edge = route[-1]
        via_edges = route[1:-1] if len(route) > 2 else []
        
        # 计算车流率 (vehsPerHour)
        avg_interval = sum(data['intervals']) / len(data['intervals'])
        vehs_per_hour = int(3600 / avg_interval) if avg_interval > 0 else 100
        
        # 获取时间范围
        min_start = min(data['start_times'])
        max_end = max(data['end_times'])
        if max_end == 0:
            max_end = 3600  # 默认结束时间
        
        # 创建 flow 元素
        flow = etree.SubElement(root, "flow")
        flow.set("id", f"f_{flow_id}")
        flow.set("departPos", "random_free")
        flow.set("from", from_edge)
        flow.set("to", to_edge)
        if via_edges:
            flow.set("via", " ".join(via_edges))
        flow.set("begin", str(int(min_start)))
        flow.set("end", str(int(max_end)))
        flow.set("vehsPerHour", str(vehs_per_hour))
        flow.set("type", "car")
        
        flow_id += 1
    
    # 写入文件
    tree = etree.ElementTree(root)
    with open(output_path, 'wb') as f:
        tree.write(f, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    
    print(f"转换完成！生成了 {flow_id} 个车流")
    return flow_id


if __name__ == "__main__":
    import os
    from silicontraffic.scityflow import load_cityflow_road_net
    
    # 定义文件路径
    cityflow_flow_path = os.path.join(
        os.path.dirname(__file__),
        'examples/data/cityflow/hangzhou/anon_4_4_hangzhou_real.json'
    )
    cityflow_roadnet_path = os.path.join(
        os.path.dirname(__file__),
        'examples/data/cityflow/hangzhou/roadnet_4_4.json'
    )
    output_path = os.path.join(
        os.path.dirname(__file__),
        'examples/data/sumo/hangzhou/roadnet_4_4.rou.xml'
    )
    
    print("开始将 CityFlow 车流转换为 SUMO 格式...")
    print(f"  加载车流文件: {cityflow_flow_path}")
    print(f"  加载路网文件: {cityflow_roadnet_path}")
    
    # 加载路网
    road_net = load_cityflow_road_net(cityflow_roadnet_path)
    
    # 转换车流
    num_flows = convert_cityflow_flow_to_sumo(cityflow_flow_path, road_net, output_path)
    
    print(f"  保存为 SUMO 格式: {output_path}")
    print(f"转换完成！生成了 {num_flows} 个车流")
