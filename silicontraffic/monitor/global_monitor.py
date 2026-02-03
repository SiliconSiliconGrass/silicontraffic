have_traci = True
try:
    import traci
    from traci.constants import VAR_LANE_ID, VAR_SPEED

except (ImportError, ModuleNotFoundError):
    have_traci = False

from ..ssumo.silicon_sumo_engine import SiliconSumoEngine
from .abstract_monitor import Monitor
from ..abstract_traffic_env_engine import TrafficEngine
from ..vehicle import Vehicle


class GlobalMonitor(Monitor):
    """
    Global stats retriever

    provides:
        - get_avg_waiting_time: float
        - get_avg_travel_time: float
        - get_avg_stop_count: float
        - get_avg_queue_length: float
    """
    def __init__(self):
        super().__init__()

    def attach_to(self, engine: TrafficEngine):
        self.engine = engine
        self.setup_auto_reset(engine)
        self.engine.on_step(lambda _: self._on_step())

        self._vehicle_waiting_time: dict[str, float] = {} # vehicle id -> accumulative waiting time
        self._vehicle_stop: dict[str, int] = {} # vehicle id -> accumulative times of stop

        self._vehicle_is_waiting: dict[str, bool] = {} # vehicle id -> whether is waiting now

        self._vehicle_depart_time: dict[str, float] = {} # vehicle id -> depart time
        self._vehicle_arrive_time: dict[str, float] = {} # vehicle id -> arrive time
        self._vehicle_travel_time_list: list[float] = []
        self._global_avg_queue_length: list[float] = [] # average queue length of all lanes (at each step)
        self._throughput = 0 # number of vehicles that arrive
    
    def reset(self):
        self._vehicle_waiting_time.clear()
        self._vehicle_stop.clear()
        self._vehicle_is_waiting.clear()
        self._vehicle_depart_time.clear()
        self._vehicle_arrive_time.clear()
        self._vehicle_travel_time_list.clear()
        self._global_avg_queue_length.clear()
        self._throughput = 0 # number of vehicles that arrive
    
    def _on_step(self):
        curr_time = self.engine.get_time()
        
        # vehicle based stats
        departed_vehicle_ids = self.engine.get_last_step_departed_vehicle_ids()
        arrived_vehicle_ids = self.engine.get_last_step_arrived_vehicle_ids()
        self._throughput += len(arrived_vehicle_ids)
        
        all_vehicle_ids = self.engine.get_vehicle_ids()

        for vehicle_id in all_vehicle_ids:

            vehicle = self.engine.get_vehicle_info(vehicle_id)

            if vehicle_id not in self._vehicle_waiting_time:
                self._vehicle_waiting_time[vehicle_id] = 0.0
            
            if vehicle_id not in self._vehicle_stop:
                self._vehicle_stop[vehicle_id] = 0
            
            if vehicle_id not in self._vehicle_is_waiting:
                self._vehicle_is_waiting[vehicle_id] = (vehicle.speed < 0.1)
            
            if vehicle.speed < 0.1:
                self._vehicle_waiting_time[vehicle_id] += 1 # record waiting time
                if not self._vehicle_is_waiting[vehicle_id]: # record the start of one stop
                    self._vehicle_stop[vehicle_id] += 1
                self._vehicle_is_waiting[vehicle_id] = True
            else:
                self._vehicle_is_waiting[vehicle_id] = False

        for vehicle_id in departed_vehicle_ids:
            # if vehicle_id in self._vehicle_depart_time:
            #     print(f"Vehicle {vehicle_id} departs more than once!")
            #     breakpoint()
            self._vehicle_depart_time[vehicle_id] = curr_time # record vehicle depart time

        for vehicle_id in arrived_vehicle_ids:
            if vehicle_id not in self._vehicle_depart_time:
                raise ValueError(f"Vehicle {vehicle_id} arrives before departure!")
            self._vehicle_travel_time_list.append(curr_time - self._vehicle_depart_time[vehicle_id])
            self._vehicle_depart_time.pop(vehicle_id)
            # self._vehicle_arrive_time[vehicle_id] = curr_time # record vehicle arrive time

        # lane based stats
        sum_queue_length = sum([self.engine.get_lane_queue_length(lane) for lane in self.engine.road_net.lanes])
        avg_queue_length = sum_queue_length / len(self.engine.road_net.lanes) if len(self.engine.road_net.lanes) > 0 else 0.0
        self._global_avg_queue_length.append(avg_queue_length)

    def get_avg_waiting_time(self) -> float:
        """
        return the average waiting time of all recorded vehicles
        """
        return sum(self._vehicle_waiting_time.values()) / len(self._vehicle_waiting_time) if len(self._vehicle_waiting_time) > 0 else 0.0
    
    def get_avg_stop_times(self) -> float:
        """
        return the average times of stop of all recorded vehicles
        """
        return sum(self._vehicle_stop.values()) / len(self._vehicle_stop) if len(self._vehicle_stop) > 0 else 0.0

    def get_avg_travel_time(self) -> float:
        """
        return the average travel time of all recorded vehicles (not including the vehicles that never arrive)
        """
        sum_travel_time = 0.0
        effective_vehicle_num = 0

        # curr_time = self.engine.get_time()

        # for vehicle_id in self._vehicle_depart_time:
        #     if vehicle_id in self._vehicle_arrive_time:
        #         sum_travel_time += self._vehicle_arrive_time[vehicle_id] - self._vehicle_depart_time[vehicle_id]
        #         effective_vehicle_num += 1
        #     else:
        #         sum_travel_time += curr_time - self._vehicle_depart_time[vehicle_id]
        #         effective_vehicle_num += 1
        
        # return sum_travel_time / effective_vehicle_num if effective_vehicle_num > 0 else 0.0

        if len(self._vehicle_travel_time_list) == 0:
            return 0
        else:
            return sum(self._vehicle_travel_time_list) / len(self._vehicle_travel_time_list)

    def get_avg_queue_length(self) -> float:
        """
        return the average queue length of all lanes
        """
        return sum(self._global_avg_queue_length) / len(self._global_avg_queue_length) if len(self._global_avg_queue_length) > 0 else 0.0

    def get_throughput(self) -> int:
        """
        return the number of vehicles that arrive
        """
        return self._throughput