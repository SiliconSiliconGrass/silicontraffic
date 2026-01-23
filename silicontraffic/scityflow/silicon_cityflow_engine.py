try:
    import cityflow
except (ImportError, ModuleNotFoundError):
    raise ImportError("CityFlow module not found. Please install CityFlow first.")

import json
import os

from .cityflow_road_net import load_cityflow_road_net
from ..abstract_traffic_env_engine import TrafficEnvEngine
from ..road_net import *
from ..vehicle import Vehicle

class SiliconCityFlowEngine(TrafficEnvEngine):
    """
    General CityFlow engine implementation
    """
    def __init__(self, path_to_cityflow_config: str, thread_num: int = 8):
        super().__init__()
        self.path_to_cityflow_config = path_to_cityflow_config
        self.thread_num = thread_num
        
        # load road net
        with open(path_to_cityflow_config, "r") as f:
            cityflow_config = json.load(f)
        path_to_road_net_file = os.path.join(os.path.dirname(path_to_cityflow_config), cityflow_config["roadnetFile"])
        self.road_net = load_cityflow_road_net(path_to_road_net_file)

        self.traffic_light_ids = list(self.road_net.traffic_light_bank.keys())

        self._cache_lane_vehicle_ids: dict[str, list[str]] = {} # lane id -> vehicle ids
        self._cache_lane_vehicle_ids_time: int = -1
        self._cache_vehicle_info: dict[str, Vehicle] = {} # vehicle id -> vehicle

        self._cache_traffic_light_phase_map: dict[str, int] = {} # traffic light id -> phase index

    def terminate(self):
        # it seems that cityflow does not need to terminate explicitly
        pass

    def reset(self):
        self.eng = cityflow.Engine(self.path_to_cityflow_config, thread_num = self.thread_num)

        self._cache_lane_vehicle_ids.clear()
        self._cache_lane_vehicle_ids_time = -1
        self._cache_vehicle_info.clear()
        self._cache_traffic_light_phase_map.clear()

    def _simulation_step(self, step_num: int = 1):
        self._cache_vehicle_info.clear()
        self.eng.next_step()
    
    def get_time(self) -> float:
        return self.eng.get_current_time()
    
    def set_traffic_light_phase(self, traffic_light: Union[str, TrafficLight], phase: Union[int, TrafficLightPhase]):
        if isinstance(traffic_light, TrafficLight):
            traffic_light = traffic_light.id
        if isinstance(phase, TrafficLightPhase):
            phase = phase.index
        self.eng.set_tl_phase(traffic_light, phase)
        self._cache_traffic_light_phase_map[traffic_light] = phase

    def get_traffic_light_phase(self, traffic_light: Union[str, TrafficLight]) -> int:
        # it seems that cityflow does not provide a method to get traffic light phase, so we cache it
        if isinstance(traffic_light, TrafficLight):
            traffic_light = traffic_light.id
        assert traffic_light in self.traffic_light_ids, f"traffic light {traffic_light} not found"
        phase_index = self._cache_traffic_light_phase_map[traffic_light]
        return self.road_net.get_traffic_light(traffic_light).phases[phase_index]

    def get_lane_vehicle_ids(self, lane: Union[str, Lane]) -> list[str]:
        if isinstance(lane, Lane):
            lane = lane.id
        
        curr_simulation_time = self.get_time()
        if self._cache_lane_vehicle_ids_time != curr_simulation_time:
            self._cache_lane_vehicle_ids = self.eng.get_lane_vehicles()
            self._cache_lane_vehicle_ids_time = curr_simulation_time
        
        assert lane in self._cache_lane_vehicle_ids, f"lane {lane} not found"
        return self._cache_lane_vehicle_ids[lane]

    def get_vehicle_info(self, vehicle_id) -> Vehicle:
        if vehicle_id in self._cache_vehicle_info:
            return self._cache_vehicle_info[vehicle_id]
        
        info_dict: dict = self.eng.get_vehicle_info(vehicle_id)

        assert "running" in info_dict, f"key 'running' not found in vehicle info dict {info_dict}"

        if not info_dict["running"]:
            vehicle = Vehicle(id=vehicle_id, running=False)
        
        else:
            lane_position = float(info_dict["distance"])
            speed = float(info_dict["speed"])
            drivable_id = info_dict["drivable"]
            route = info_dict["route"].split(" ")
            vehicle = Vehicle(
                id=vehicle_id,
                running=True,
                lane_position=lane_position,
                speed=speed,
                drivable_id=drivable_id,
                route=route
            )
        
        self._cache_vehicle_info[vehicle_id] = vehicle
        return vehicle
