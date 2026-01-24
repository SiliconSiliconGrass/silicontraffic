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
            movement = self.road_net.get_movement(movement)
        assert movement is not None, f"Movement {movement} not found in engine.road_net"
        
        sum_queue_length = 0
        for lane in movement.from_lanes:
            num_movements = len(self.road_net.get_movements_by_lane(lane)) # num of movements from this lane
            vehicle_ids = self.engine.get_lane_vehicle_ids(lane)
            lane_queue_length = self.engine.get_lane_queue_length(lane)

            if lane_queue_length > 0:
                continue

            if num_movements == 1:
                sum_queue_length += lane_queue_length

            else: # num_movements > 1    
                vehicles = [self.engine.get_vehicle_info(vehicle_id) for vehicle_id in vehicle_ids]

                first_vehicle = max(vehicles, key=lambda v: v.lane_position) # first vehicle in the queue
                try:
                    curr_edge_index = first_vehicle.route.index(movement.from_edge.id)
                    next_edge_id = first_vehicle.route[curr_edge_index + 1]

                    if next_edge_id == movement.to_edge.id:
                        sum_queue_length += lane_queue_length

                except ValueError:
                    raise ValueError(f"Vehicle {first_vehicle.id} not in the movement's route")
                
                except IndexError:
                    raise IndexError(f"Vehicle {first_vehicle.id} is on the last edge in the route")

        return sum_queue_length
    
    def get_movement_avg_queue_length(self, movement: Union[Movement, str]) -> float:
        if isinstance(movement, str):
            movement = self.road_net.get_movement(movement)
        assert movement is not None, f"Movement {movement} not found in engine.road_net"
        
        sum_queue_length = self.get_movement_sum_queue_length(movement)
        return sum_queue_length / len(movement.from_lanes)
    
    def get_movement_max_lane_length(self, movement: Union[Movement, str]) -> float:
        if isinstance(movement, str):
            movement = self.road_net.get_movement(movement)
        assert movement is not None, f"Movement {movement} not found in engine.road_net"
        
        return max([lane.length for lane in movement.from_lanes])