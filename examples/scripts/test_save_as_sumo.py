"""
测试 save_as_sumo 功能
"""
import sys
sys.path.insert(0, '/Users/indexerror/Documents/MyStuff/Projects/__Research/code/silicon-traffic-env')

from silicontraffic.road_net.road_net import RoadNet, Junction, Edge, Lane, LaneLink, TrafficLight, TrafficLightPhase
from silicontraffic.save_net import save_as_sumo

def test_simple_network():
    """测试简单的道路网络"""
    print("测试1: 简单道路网络")
    net = RoadNet()

    # 创建两个交叉口
    j1 = Junction(id='J1', position=(0, 0))
    j2 = Junction(id='J2', position=(100, 0))
    net.junction_bank['J1'] = j1
    net.junction_bank['J2'] = j2

    # 创建一条边
    e1 = Edge(id='E1', from_junction=j1, to_junction=j2)
    net.edge_bank['E1'] = e1

    # 创建车道
    lane1 = Lane(id='E1_0', parent_edge=e1, index=0, length=100.0, speed_limit=13.89)
    lane1.shape = [(0, 0), (100, 0)]
    e1.lanes.append(lane1)
    net.lane_bank['E1_0'] = lane1

    # 添加边到交叉口
    j1.out_going_edges.append(e1)
    j2.in_coming_edges.append(e1)

    # 保存为SUMO格式
    output_path = '/Users/indexerror/Documents/MyStuff/Projects/__Research/code/silicon-traffic-env/examples/data/sumo/test/test_simple_output.net.xml'
    save_as_sumo(net, output_path)
    print(f"  保存成功: {output_path}")


def test_network_with_traffic_light():
    """测试带交通灯的道路网络"""
    print("\n测试2: 带交通灯的道路网络")
    net = RoadNet()

    # 创建交叉口
    j1 = Junction(id='J1', position=(0, 0))
    j2 = Junction(id='J2', position=(100, 0))
    j3 = Junction(id='J3', position=(100, 100))
    net.junction_bank['J1'] = j1
    net.junction_bank['J2'] = j2
    net.junction_bank['J3'] = j3

    # 创建边
    e1 = Edge(id='E1', from_junction=j1, to_junction=j2)
    e2 = Edge(id='E2', from_junction=j2, to_junction=j3)
    net.edge_bank['E1'] = e1
    net.edge_bank['E2'] = e2

    # 创建车道
    lane1 = Lane(id='E1_0', parent_edge=e1, index=0, length=100.0, speed_limit=13.89)
    lane1.shape = [(0, 0), (100, 0)]
    e1.lanes.append(lane1)
    net.lane_bank['E1_0'] = lane1

    lane2 = Lane(id='E2_0', parent_edge=e2, index=0, length=100.0, speed_limit=13.89)
    lane2.shape = [(100, 0), (100, 100)]
    e2.lanes.append(lane2)
    net.lane_bank['E2_0'] = lane2

    # 创建内部边（连接车道）
    internal_edge = Edge(id=':J2_0', from_junction=j2, to_junction=j2)
    internal_lane = Lane(id=':J2_0_0', parent_edge=internal_edge, index=0, length=5.0)
    internal_edge.lanes.append(internal_lane)
    net.edge_bank[':J2_0'] = internal_edge
    net.lane_bank[':J2_0_0'] = internal_lane

    # 创建连接
    lane_link = LaneLink(from_lane=lane1, to_lane=lane2, link_lane=internal_lane)
    j2.lane_links.append(lane_link)

    # 添加边到交叉口
    j1.out_going_edges.append(e1)
    j2.in_coming_edges.append(e1)
    j2.out_going_edges.append(e2)
    j3.in_coming_edges.append(e2)

    # 创建交通灯
    tl = TrafficLight(id='J2', controlled_links=[lane_link], phases=[])
    phase1 = TrafficLightPhase(index=0, duration=30, parent_trafficlight=tl, available_links=[lane_link])
    phase2 = TrafficLightPhase(index=1, duration=5, parent_trafficlight=tl, available_links=[])
    phase3 = TrafficLightPhase(index=2, duration=30, parent_trafficlight=tl, available_links=[])
    tl.phases = [phase1, phase2, phase3]
    net.traffic_light_bank['J2'] = tl

    # 保存为SUMO格式
    output_path = '/Users/indexerror/Documents/MyStuff/Projects/__Research/code/silicon-traffic-env/examples/data/sumo/test/test_traffic_light_output.net.xml'
    save_as_sumo(net, output_path)
    print(f"  保存成功: {output_path}")


def test_complex_network():
    """测试复杂的道路网络（十字路口）"""
    print("\n测试3: 复杂道路网络（十字路口）")
    net = RoadNet()

    # 创建交叉口（十字路口）
    center = Junction(id='center', position=(100, 100))
    north = Junction(id='north', position=(100, 200))
    south = Junction(id='south', position=(100, 0))
    east = Junction(id='east', position=(200, 100))
    west = Junction(id='west', position=(0, 100))
    
    net.junction_bank['center'] = center
    net.junction_bank['north'] = north
    net.junction_bank['south'] = south
    net.junction_bank['east'] = east
    net.junction_bank['west'] = west

    # 创建边
    e_north = Edge(id='E_north', from_junction=center, to_junction=north)
    e_south = Edge(id='E_south', from_junction=center, to_junction=south)
    e_east = Edge(id='E_east', from_junction=center, to_junction=east)
    e_west = Edge(id='E_west', from_junction=center, to_junction=west)
    
    e_north_in = Edge(id='E_north_in', from_junction=north, to_junction=center)
    e_south_in = Edge(id='E_south_in', from_junction=south, to_junction=center)
    e_east_in = Edge(id='E_east_in', from_junction=east, to_junction=center)
    e_west_in = Edge(id='E_west_in', from_junction=west, to_junction=center)
    
    net.edge_bank['E_north'] = e_north
    net.edge_bank['E_south'] = e_south
    net.edge_bank['E_east'] = e_east
    net.edge_bank['E_west'] = e_west
    net.edge_bank['E_north_in'] = e_north_in
    net.edge_bank['E_south_in'] = e_south_in
    net.edge_bank['E_east_in'] = e_east_in
    net.edge_bank['E_west_in'] = e_west_in

    # 创建车道
    for edge, shape in [
        (e_north, [(100, 100), (100, 200)]),
        (e_south, [(100, 100), (100, 0)]),
        (e_east, [(100, 100), (200, 100)]),
        (e_west, [(100, 100), (0, 100)]),
        (e_north_in, [(100, 200), (100, 100)]),
        (e_south_in, [(100, 0), (100, 100)]),
        (e_east_in, [(200, 100), (100, 100)]),
        (e_west_in, [(0, 100), (100, 100)]),
    ]:
        lane = Lane(id=f'{edge.id}_0', parent_edge=edge, index=0, length=100.0, speed_limit=13.89)
        lane.shape = shape
        edge.lanes.append(lane)
        net.lane_bank[lane.id] = lane

    # 添加边到交叉口
    center.out_going_edges.extend([e_north, e_south, e_east, e_west])
    center.in_coming_edges.extend([e_north_in, e_south_in, e_east_in, e_west_in])
    north.in_coming_edges.append(e_north)
    north.out_going_edges.append(e_north_in)
    south.in_coming_edges.append(e_south)
    south.out_going_edges.append(e_south_in)
    east.in_coming_edges.append(e_east)
    east.out_going_edges.append(e_east_in)
    west.in_coming_edges.append(e_west)
    west.out_going_edges.append(e_west_in)

    # 创建交通灯
    controlled_links = []
    for in_edge in [e_north_in, e_south_in, e_east_in, e_west_in]:
        for out_edge in [e_north, e_south, e_east, e_west]:
            if in_edge != out_edge:
                # 创建内部车道
                internal_edge_id = f':center_{len(controlled_links)}'
                internal_edge = Edge(id=internal_edge_id, from_junction=center, to_junction=center)
                internal_lane = Lane(id=f'{internal_edge_id}_0', parent_edge=internal_edge, index=0, length=10.0)
                internal_edge.lanes.append(internal_lane)
                net.edge_bank[internal_edge_id] = internal_edge
                net.lane_bank[internal_lane.id] = internal_lane
                
                # 创建连接
                lane_link = LaneLink(
                    from_lane=in_edge.lanes[0], 
                    to_lane=out_edge.lanes[0], 
                    link_lane=internal_lane
                )
                center.lane_links.append(lane_link)
                controlled_links.append(lane_link)

    tl = TrafficLight(id='center', controlled_links=controlled_links, phases=[])
    # 简单的两相位交通灯
    phase1 = TrafficLightPhase(index=0, duration=30, parent_trafficlight=tl, available_links=controlled_links[:len(controlled_links)//2])
    phase2 = TrafficLightPhase(index=1, duration=30, parent_trafficlight=tl, available_links=controlled_links[len(controlled_links)//2:])
    tl.phases = [phase1, phase2]
    net.traffic_light_bank['center'] = tl

    # 保存为SUMO格式
    output_path = '/Users/indexerror/Documents/MyStuff/Projects/__Research/code/silicon-traffic-env/examples/data/sumo/test/test_complex_output.net.xml'
    save_as_sumo(net, output_path)
    print(f"  保存成功: {output_path}")


if __name__ == '__main__':
    test_simple_network()
    test_network_with_traffic_light()
    test_complex_network()
    print("\n所有测试完成！")
