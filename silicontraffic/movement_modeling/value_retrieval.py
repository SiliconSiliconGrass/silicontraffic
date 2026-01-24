from .movement import Movement
from ..abstract_traffic_env_engine import TrafficEngine

def get_movement_sum_queue_length(engine: TrafficEngine, movement: Movement) -> int:
    """
    Get the queue length of the given movement.
    """
    for lane in movement.from_lanes:
        vehicles = engine.get_lane_vehicle_ids(lane)
