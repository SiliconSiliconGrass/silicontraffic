import json
from typing import Literal
from ..road_net import *

def _get_road_length(points):
    l = 0
    for i in range(len(points) - 1):
        l += ((points[i]['x'] - points[i+1]['x'])**2 + (points[i]['y'] - points[i+1]['y'])**2)**0.5
    return l

def load_cityflow_road_net(road_net_file_path: str) -> RoadNet:
    with open(road_net_file_path, 'r') as f:
        road_net_data = json.load(f)

    road_net = RoadNet()
    
    # 1. Create Intersections
    for inter_data in road_net_data['intersections']:
        inter_id = inter_data['id']
        point = inter_data['point']
        # width = inter_data['width']
        # road_ids = inter_data['roads']
        # road_links = inter_data['roadLinks']
        # traffic_light_phase = inter_data['trafficLight']
        # virtual = inter_data['virtual']

        intersection = Junction(
            id=inter_id,
            position=point,
            in_coming_edges=[], # see below
            out_going_edges=[]  # see below
        )
        road_net.junction_bank[inter_id] = intersection
    
    # 2. Create Roads And Lanes
    for road_data in road_net_data['roads']:
        road_id = road_data['id']
        # points = road_data['points']
        list_lane_data = road_data['lanes']
        start_inter_id = road_data['startIntersection']
        end_inter_id = road_data['endIntersection']
        road_points: list[dict[Literal['x', 'y'], float]] = road_data['points']
        road_length = _get_road_length(road_points)

        road = Edge(
            id=road_id,
            from_junction=road_net.junction_bank[start_inter_id],
            to_junction=road_net.junction_bank[end_inter_id],
            lanes=[]
        )

        list_lanes = []
        for i, lane_data in enumerate(list_lane_data):
            lane_id = f'{road_id}_{i}'
            width = lane_data['width']
            max_speed = lane_data['maxSpeed']
            lane = Lane(
                id=lane_id,
                parent_edge=road,
                index=i,
                width=width,
                speed_limit=max_speed,
                length=road_length
            )
            road_net.lane_bank[lane_id] = lane
            list_lanes.append(lane)
        
        road.lanes = list_lanes
        road_net.edge_bank[road_id] = road

    # 3. Add Roads Access To Intersections
    for inter_data in road_net_data['intersections']:
        inter_id = inter_data['id']
        road_ids = inter_data['roads']

        for road_id in road_ids:
            if road_id not in road_net.edge_bank:
                raise RuntimeError(f"Road {road_id} referenced in intersection {inter_id} not found in edge_bank.")
            
            road = road_net.edge_bank[road_id]
            if road.from_junction.id == inter_id:
                road_net.junction_bank[inter_id].out_going_edges.append(road)
            elif road.to_junction.id == inter_id:
                road_net.junction_bank[inter_id].in_coming_edges.append(road)
            else:
                raise RuntimeError(f"Trying to connect road {road_id} to intersection {inter_id}, but neither end matches this intersection.")
    
    # 4. Build Traffic Light And Lane Link Data
    for inter_data in road_net_data['intersections']:

        traffic_light = TrafficLight(
            id=inter_data['id'],
            controlled_links=[],
            phases=[]
        )

        list_road_link_data = inter_data['roadLinks']
        traffic_light_data = inter_data['trafficLight']

        # 4.1 build lane links
        links: list[LaneLink] = []

        for road_link_data in list_road_link_data:
            start_road_id = road_link_data['startRoad']
            end_road_id = road_link_data['endRoad']

            link_type = None
            if 'type' in road_link_data:
                link_type = road_link_data['type']

            for lane_link_data in road_link_data['laneLinks']:
                start_lane_index = lane_link_data['startLaneIndex']
                end_lane_index = lane_link_data['endLaneIndex']

                start_lane_id = f'{start_road_id}_{start_lane_index}'
                end_lane_id = f'{end_road_id}_{end_lane_index}'

                link = LaneLink(
                    from_lane=road_net.lane_bank[start_lane_id],
                    to_lane=road_net.lane_bank[end_lane_id],
                    link_lane=None, # TODO: add link lane if necessary
                    type=link_type
                )
                links.append(link)
                link.from_lane.links.append(link)
        
        road_net.junction_bank[traffic_light.id].lane_links = links
        if len(traffic_light_data['roadLinkIndices']) == 0:
            # unsignalized intersection
            continue
    
        # 4.2 create traffic light phases
        phases: list[TrafficLightPhase] = []
        road_link_indices = traffic_light_data['roadLinkIndices']
        list_phase_data = traffic_light_data['lightphases']

        for i, phase_data in enumerate(list_phase_data):
            time = phase_data['time']
            available_road_link_ids = phase_data['availableRoadLinks']
            available_links = []
            for link_id in available_road_link_ids:
                road_link_data = list_road_link_data[ road_link_indices[link_id] ] # TODO: Is it correct?
                for link in links:
                    if link.from_lane.parent_edge.id == road_link_data['startRoad'] and link.to_lane.parent_edge.id == road_link_data['endRoad']:
                        available_links.append(link)

            phase = TrafficLightPhase(
                index=i,
                duration=time,
                parent_trafficlight=traffic_light,
                available_links=available_links
            )
            phases.append(phase)
        
        traffic_light.controlled_links = links
        traffic_light.phases = phases

        road_net.traffic_light_bank[traffic_light.id] = traffic_light

    return road_net
