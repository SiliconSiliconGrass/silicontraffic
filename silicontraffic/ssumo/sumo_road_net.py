try:
    import sumolib
except (ImportError, ModuleNotFoundError):
    raise ImportError("sumolib module not found. Please install sumo first.")

from ..road_net import *

def load_sumo_road_net(path_to_road_net_file: str) -> RoadNet:
    """
    Load SUMO road net from file
    """
    sumo_net: sumolib.net.Net = sumolib.net.readNet(path_to_road_net_file, withPrograms=True)


    junction_bank: dict[str, Junction] = {}
    edge_bank: dict[str, Edge] = {}
    lane_bank: dict[str, Lane] = {}
    trafficlight_bank: dict[str, TrafficLight] = {}

    nodes: list[sumolib.net.node.Node] = sumo_net.getNodes()
    for node in nodes:
        node_id = node.getID()
        junction_bank[node_id] = Junction(node_id, node.getCoord(), shape=node.getShape())
    
    edges: list[sumolib.net.edge.Edge] = sumo_net.getEdges()
    for edge in edges:
        edge_id = edge.getID()

        from_node: sumolib.net.node.Node = edge.getFromNode()
        to_node: sumolib.net.node.Node = edge.getToNode()
        
        from_junction_id: str = from_node.getID()
        to_junction_id: str = to_node.getID()

        assert from_junction_id in junction_bank, f"Junction {from_junction_id} not found in junction bank"
        assert to_junction_id in junction_bank, f"Junction {to_junction_id} not found in junction bank"

        from_junction_obj = junction_bank[from_junction_id]
        to_junction_obj = junction_bank[to_junction_id]

        edge_obj = Edge(edge_id, from_junction_obj, to_junction_obj, edge_type=edge.getType())
        edge_bank[edge_id] = edge_obj

        from_junction_obj.out_going_edges.append(edge_obj)
        to_junction_obj.in_coming_edges.append(edge_obj)

        lanes: list[sumolib.net.lane.Lane] = edge.getLanes() # lanes of the edge
        for lane in lanes:
            lane_id = lane.getID()
            lane_obj = Lane(lane_id, edge_obj, lane.getIndex(), length=lane.getLength(), width=lane.getWidth(), speed_limit=lane.getSpeed(), shape=lane.getShape())
            lane_bank[lane_id] = lane_obj
            edge_obj.lanes.append(lane_obj)
    
    # build lane links
    for node in nodes:
        node_id = node.getID()
        junction_obj = junction_bank[node_id]
        connections: list[sumolib.net.connection.Connection] = node.getConnections()
        for connection in connections:
            from_lane_id: str = connection.getFromLane().getID()
            to_lane_id: str = connection.getToLane().getID()

            assert from_lane_id in lane_bank, f"Lane {from_lane_id} not found in lane bank"
            assert to_lane_id in lane_bank, f"Lane {to_lane_id} not found in lane bank"

            from_lane_obj = lane_bank[from_lane_id]
            to_lane_obj = lane_bank[to_lane_id]
            lane_link_obj = LaneLink(from_lane_obj, to_lane_obj, link_lane=None)
            from_lane_obj.links.append(lane_link_obj)
            junction_obj.lane_links.append(lane_link_obj)
    
    traffic_lights: list[sumolib.net.TLS] = sumo_net.getTrafficLights()
    for traffic_light in traffic_lights:
        traffic_light_id = traffic_light.getID()

        tl_connections: list[tuple[sumolib.net.lane.Lane, sumolib.net.lane.Lane, int]] = traffic_light.getConnections()
        
        link_objs = [None for _ in range(len(tl_connections))]

        for connection in tl_connections:
            from_lane, to_lane, link_index = connection
            from_lane_obj = lane_bank[from_lane.getID()]
            to_lane_obj = lane_bank[to_lane.getID()]
            link_objs[link_index] = LaneLink(from_lane_obj, to_lane_obj, link_lane=None) # to ensure the order of lane links

        traffic_light_program: sumolib.net.TLSProgram = traffic_light.getPrograms()["0"] # using the default program
        traffic_light_phases: list[sumolib.net.Phase] = traffic_light_program.getPhases()

        trafficlight_obj = TrafficLight(traffic_light_id, controlled_links=link_objs, phases=[])

        for i, phase in enumerate(traffic_light_phases):

            available_links = []
            for state_char, link_obj in zip(phase.state, trafficlight_obj.controlled_links):
                if state_char.upper() == 'G':
                    available_links.append(link_obj)

            phase_obj = TrafficLightPhase(index=i, duration=phase.duration, parent_trafficlight=trafficlight_obj, available_links=available_links)
            trafficlight_obj.phases.append(phase_obj)

        trafficlight_bank[traffic_light_id] = trafficlight_obj

    road_net = RoadNet(junction_bank, edge_bank, lane_bank, trafficlight_bank)
    return road_net
