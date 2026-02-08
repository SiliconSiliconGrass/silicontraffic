from .abstract_monitor import Monitor
from ..abstract_traffic_env_engine import TrafficEngine
from ..movement_modeling import Movement, MovementRoadNet

from typing import Union

class MovementsMonitor(Monitor):
    """
    Data retriever for movements
    """
    def __init__(self):
        super().__init__()

    def attach_to(self, engine: TrafficEngine):
        self.engine = engine
        # self.setup_auto_reset(engine)

        try:
            self.road_net = MovementRoadNet(engine.road_net)
        except Exception as e:
            raise ValueError("Failed to create MovementRoadNet from engine.road_net") from e
        
    def reset(self):
        pass
    
    def get_movement_sum_queue_length(self, movement: Union[Movement, str]) -> int:
        if isinstance(movement, str):
            movement = self.road_net.movement_bank.get(movement)
        assert movement is not None, f"Movement {movement} not found in engine.road_net"
        
        sum_queue_length = 0
        for lane in movement.from_lanes:
            num_movements = len(self.road_net.get_movements_by_lane(lane)) # num of movements from this lane
            vehicle_ids = self.engine.get_lane_vehicle_ids(lane)
            lane_queue_length = self.engine.get_lane_queue_length(lane)

            if lane_queue_length == 0:
                continue

            if num_movements == 1:
                sum_queue_length += lane_queue_length

            else: # num_movements > 1    
                vehicles = [self.engine.get_vehicle_info(vehicle_id) for vehicle_id in vehicle_ids]

                first_vehicle = max(vehicles, key=lambda v: v.lane_position) # first vehicle in the queue

                if movement.from_edge.id not in first_vehicle.route:
                    raise ValueError(f"Vehicle {first_vehicle.id} not in the movement's route")

                curr_edge_index = first_vehicle.route.index(movement.from_edge.id)

                if curr_edge_index == len(first_vehicle.route) - 1:
                    # raise IndexError(f"Vehicle {first_vehicle.id} is on the last edge in the route")

                    first_vehicle = None
                    curr_edge_index = None

                    sorted_vehicles = sorted(vehicles, key=lambda v: -v.lane_position) # the first vehicle in the queue is the one with the biggest lane_position
                    sorted_vehicles = sorted_vehicles[1:]
                    if len(sorted_vehicles) == 0:
                        continue
                    for vehicle in sorted_vehicles:
                        if movement.from_edge.id not in vehicle.route:
                            raise ValueError(f"Vehicle {first_vehicle.id} not in the movement's route")
                        
                        curr_edge_index = vehicle.route.index(movement.from_edge.id)

                        if curr_edge_index < len(vehicle.route) - 1:
                            # effective first vehicle
                            first_vehicle = vehicle
                            break

                if first_vehicle is None:
                    continue

                next_edge_id = first_vehicle.route[curr_edge_index + 1]

                if next_edge_id == movement.to_edge.id:
                    sum_queue_length += lane_queue_length
        return sum_queue_length
    
    def get_movement_avg_queue_length(self, movement: Union[Movement, str]) -> float:
        if isinstance(movement, str):
            movement = self.road_net.movement_bank.get(movement)
        assert movement is not None, f"Movement {movement} not found in engine.road_net"
        
        sum_queue_length = self.get_movement_sum_queue_length(movement)
        return sum_queue_length / len(movement.from_lanes)
    
    def get_movement_max_lane_length(self, movement: Union[Movement, str]) -> float:
        if isinstance(movement, str):
            movement = self.road_net.movement_bank.get(movement)
        assert movement is not None, f"Movement {movement} not found in engine.road_net"
        
        return max([lane.length for lane in movement.from_lanes])
    
    def get_movement_effective_vehicles(self, movement: Union[Movement, str], effective_range: float = 100) -> int:
        if isinstance(movement, str):
            movement = self.road_net.movement_bank.get(movement)
        assert movement is not None, f"Movement {movement} not found in engine.road_net"
        
        list_lane_effective_vehicles = []
        for lane in movement.from_lanes:
            # TODO: check movement demand
            lane_effective_vehicles = 0
            vehicle_ids = self.engine.get_lane_vehicle_ids(lane)
            for vehicle_id in vehicle_ids:
                vehicle = self.engine.get_vehicle_info(vehicle_id)
                if lane.length - vehicle.lane_position > effective_range:
                    continue
                lane_effective_vehicles += 1
            list_lane_effective_vehicles.append(lane_effective_vehicles)

        movement_effective_vehicles = sum(list_lane_effective_vehicles) / len(movement.from_lanes) if len(movement.from_lanes) > 0 else 0
        return movement_effective_vehicles

    def get_movement_efficient_pressure(self, movement: Union[Movement, str]) -> float:
        if isinstance(movement, str):
            movement = self.road_net.get_movement(movement)
        assert movement is not None, f"Movement {movement} not found in engine.road_net"
        
        upstream_avg_queue_length = self.get_movement_avg_queue_length(movement)

        list_downstream_avg_queue_length = []
        for downstream_movement in self.road_net.get_downstream_movements(movement):
            list_downstream_avg_queue_length.append(self.get_movement_avg_queue_length(downstream_movement))
        downstream_avg_queue_length = sum(list_downstream_avg_queue_length) / len(self.road_net.get_downstream_movements(movement)) \
            if len(self.road_net.get_downstream_movements(movement)) > 0 else 0
        
        pressure = upstream_avg_queue_length - downstream_avg_queue_length
        return pressure
