from .abstract_monitor import Monitor
from ..abstract_traffic_env_engine import TrafficEngine
from ..movement_modeling import Movement, MovementRoadNet
from ..road_net import ExtendedLane

from typing import Union

class MovementsMonitor(Monitor):
    """
    Data retriever for movements
    """
    def __init__(self):
        super().__init__()

    def attach_to(self, engine: TrafficEngine, extended_road_net=None):
        self.engine = engine
        # self.setup_auto_reset(engine)
        self.extended_road_net = extended_road_net
        self.incoming_lane_map = {}
        if extended_road_net is not None:
            self.incoming_lane_map = dict(getattr(extended_road_net, "incoming_lane_map", {}))

        try:
            self.road_net = MovementRoadNet(engine.road_net)
        except Exception as e:
            raise ValueError("Failed to create MovementRoadNet from engine.road_net") from e
        
    def reset(self):
        pass


    def set_extended_road_net(self, extended_road_net) -> None:
        """
        Attach the extended-lane view (usually the env's simplified road net)
        after `attach_to`. Queue / effective-vehicle statistics of a movement
        then use the extended lane-like of each `from_lane` (an extended lane
        aggregates all its constituent lanes).
        """
        self.extended_road_net = extended_road_net
        self.incoming_lane_map = dict(getattr(extended_road_net, "incoming_lane_map", {}))


    def _extended_of(self, lane):
        """ExtendedLane of `lane` if it has one, else the lane itself."""
        ext = self.incoming_lane_map.get(lane.id)
        return ext if ext is not None else lane


    def _movement_lane_likes(self, movement) -> list:
        """Deduped lane-likes (Lane | ExtendedLane) of a movement's from_lanes."""
        result = []
        seen = set()
        for lane in movement.from_lanes:
            lane_like = self._extended_of(lane)
            if lane_like.id in seen:
                continue
            seen.add(lane_like.id)
            result.append(lane_like)
        return result


    def _lane_queue_length_for_movement(self, lane, movement) -> int:
        """
        Queue length of a single lane attributed to `movement` (original
        FRAP-style logic: when a lane feeds several movements, only count the
        queue when the front vehicle is going to take this movement).
        """
        num_movements = len(self.road_net.get_movements_by_lane(lane))
        lane_queue_length = self.engine.get_lane_queue_length(lane)

        if lane_queue_length == 0:
            return 0

        if num_movements == 1:
            return lane_queue_length

        vehicle_ids = self.engine.get_lane_vehicle_ids(lane)
        vehicles = [self.engine.get_vehicle_info(vehicle_id) for vehicle_id in vehicle_ids]

        first_vehicle = max(vehicles, key=lambda v: v.lane_position)  # first vehicle in the queue

        if movement.from_edge.id not in first_vehicle.route:
            raise ValueError(f"Vehicle {first_vehicle.id} not in the movement's route")

        curr_edge_index = first_vehicle.route.index(movement.from_edge.id)

        if curr_edge_index == len(first_vehicle.route) - 1:
            first_vehicle = None
            curr_edge_index = None

            sorted_vehicles = sorted(vehicles, key=lambda v: -v.lane_position)  # the first vehicle in the queue is the one with the biggest lane_position
            sorted_vehicles = sorted_vehicles[1:]
            if len(sorted_vehicles) == 0:
                return 0
            for vehicle in sorted_vehicles:
                if movement.from_edge.id not in vehicle.route:
                    raise ValueError(f"Vehicle {first_vehicle.id} not in the movement's route")

                curr_edge_index = vehicle.route.index(movement.from_edge.id)

                if curr_edge_index < len(vehicle.route) - 1:
                    # effective first vehicle
                    first_vehicle = vehicle
                    break

        if first_vehicle is None:
            return 0

        next_edge_id = first_vehicle.route[curr_edge_index + 1]
        if next_edge_id == movement.to_edge.id:
            return lane_queue_length
        return 0
    
    def get_movement_sum_queue_length(self, movement: Union[Movement, str]) -> int:
        if isinstance(movement, str):
            movement = self.road_net.movement_bank.get(movement)
        assert movement is not None, f"Movement {movement} not found in engine.road_net"

        sum_queue_length = 0
        for lane_like in self._movement_lane_likes(movement):
            if isinstance(lane_like, ExtendedLane):
                # head lane keeps the movement-attribution logic; the upstream
                # lanes are fully attributed to this movement
                sum_queue_length += self._lane_queue_length_for_movement(lane_like.head_lane, movement)
                for lane in lane_like.lanes:
                    if lane.id == lane_like.head_lane.id:
                        continue
                    sum_queue_length += self.engine.get_lane_queue_length(lane)
            else:
                sum_queue_length += self._lane_queue_length_for_movement(lane_like, movement)
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
        for lane_like in self._movement_lane_likes(movement):
            lane_effective_vehicles = 0
            if isinstance(lane_like, ExtendedLane):
                lane_ids = {lane.id for lane in lane_like.lanes}
                for lane in lane_like.lanes:
                    tail_distance = self._tail_distance_to_head(lane, lane_like.head_lane, lane_ids)
                    vehicle_ids = self.engine.get_lane_vehicle_ids(lane)
                    for vehicle_id in vehicle_ids:
                        vehicle = self.engine.get_vehicle_info(vehicle_id)
                        distance_to_stop_line = (lane.length - vehicle.lane_position) + tail_distance
                        if distance_to_stop_line > effective_range:
                            continue
                        lane_effective_vehicles += 1
            else:
                lane = lane_like
                # TODO: check movement demand
                vehicle_ids = self.engine.get_lane_vehicle_ids(lane)
                for vehicle_id in vehicle_ids:
                    vehicle = self.engine.get_vehicle_info(vehicle_id)
                    if lane.length - vehicle.lane_position > effective_range:
                        continue
                    lane_effective_vehicles += 1
            list_lane_effective_vehicles.append(lane_effective_vehicles)

        movement_effective_vehicles = sum(list_lane_effective_vehicles) / len(movement.from_lanes) if len(movement.from_lanes) > 0 else 0
        return movement_effective_vehicles


    def _tail_distance_to_head(self, lane, head_lane, lane_ids, memo=None) -> float:
        """
        Distance from the *end* of `lane` to the stop line (the end of
        `head_lane`), following outgoing lanes that belong to the same
        extended lane. Returns 0 for the head lane itself.
        """
        if memo is None:
            memo = {}
        if lane.id in memo:
            return memo[lane.id]
        if lane.id == head_lane.id:
            memo[lane.id] = 0.0
            return 0.0
        for next_lane in lane.outgoing_lanes:
            if next_lane.id not in lane_ids:
                continue
            tail = self._tail_distance_to_head(next_lane, head_lane, lane_ids, memo)
            if tail is not None:
                memo[lane.id] = next_lane.length + tail
                return memo[lane.id]
        memo[lane.id] = None
        return None

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
