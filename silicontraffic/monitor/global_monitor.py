from ..ssumo.silicon_sumo_engine import SiliconSumoEngine
from .abstract_monitor import Monitor
from ..abstract_traffic_env_engine import TrafficEnvEngine
from ..vehicle import Vehicle

class GlobalMonitor(Monitor):
    """
    Global stats retriever
    """
    def __init__(self):
        super().__init__()

    def attach_to(self, engine: TrafficEnvEngine):
        self.engine = engine
        self.setup_auto_reset(engine)

        if isinstance(engine, SiliconSumoEngine):
            self.engine.on_step(lambda _: self._on_step_sumo())
        else:
            self.engine.on_step(lambda _: self._on_step())

        self.vehicle_bank: dict[str, Vehicle] = {} # vehicle id -> vehicle

        self._vehicle_waiting_time: dict[str, float] = {} # vehicle id -> accumulative waiting time
        self._vehicle_stop: dict[str, int] = {} # vehicle id -> accumulative times of stop

        self._vehicle_is_waiting: dict[str, bool] = {} # vehicle id -> whether is waiting now

        self._vehicle_depart_time: dict[str, float] = {} # vehicle id -> depart time
        self._vehicle_arrive_time: dict[str, float] = {} # vehicle id -> arrive time
        self._global_avg_queue_length: list[float] = [] # average queue length of all lanes (at each step)
    
    def reset(self):
        self.vehicle_bank.clear()
        self._vehicle_waiting_time.clear()
        self._vehicle_stop.clear()
        self._vehicle_is_waiting.clear()
        self._vehicle_depart_time.clear()
        self._vehicle_arrive_time.clear()

    def _on_step(self):
        curr_time = self.engine.get_time()

        # vehicle based stats
        for lane in self.engine.road_net.lanes:
            vehicle_ids = self.engine.get_lane_vehicle_ids(lane)
            for vehicle_id in vehicle_ids:
                vehicle = self.engine.get_vehicle_info(vehicle_id)

                if not vehicle.running: # vehicles not running
                    if vehicle_id in self._vehicle_depart_time and vehicle_id not in self._vehicle_arrive_time:
                        self._vehicle_arrive_time[vehicle_id] = curr_time # record arrive time

                        print(f"vehicle {vehicle_id} arrive at {curr_time}") # DEBUG
                    continue

                if vehicle_id not in self.vehicle_bank:
                    # create new vehicle record
                    self.vehicle_bank[vehicle_id] = vehicle
                    self._vehicle_waiting_time[vehicle_id] = 0.0
                    self._vehicle_stop[vehicle_id] = 0
                    self._vehicle_is_waiting[vehicle_id] = False
                    self._vehicle_depart_time[vehicle_id] = curr_time # record depart time
                else:
                    self.vehicle_bank[vehicle_id].speed = vehicle.speed

                    prev_waiting = self._vehicle_is_waiting[vehicle_id]
                    curr_waiting = (vehicle.speed < 0.1)

                    if (not prev_waiting) and curr_waiting:
                        self._vehicle_stop[vehicle_id] += 1 # record the start of a stop
                    if curr_waiting:
                        self._vehicle_waiting_time[vehicle_id] += 1 # record the waiting time
                    
                    self._vehicle_is_waiting[vehicle_id] = curr_waiting # update waiting status

        # lane based stats
        sum_queue_length = sum([self.engine.get_lane_queue_length(lane) for lane in self.engine.road_net.lanes])
        avg_queue_length = sum_queue_length / len(self.engine.road_net.lanes) if len(self.engine.road_net.lanes) > 0 else 0.0
        self._global_avg_queue_length.append(avg_queue_length)
    
    def _on_step_sumo(self):
        # optimize for sumo
        curr_time = self.engine.get_time()

        assert isinstance(self.engine, SiliconSumoEngine)

        all_reachable_vehicle_ids = self.engine.vehicle.getIDList()

        departed_vehicle_ids = self.engine.simulation.getDepartedIDList()
        arrived_vehicle_ids = self.engine.simulation.getArrivedIDList()
    

        for vehicle_id in departed_vehicle_ids:
            if vehicle_id not in self._vehicle_depart_time:
                depart_time = self.engine.vehicle.getDeparture(vehicle_id)
                # print(f"vehicle {vehicle_id} depart at {depart_time}") # DEBUG
                self._vehicle_depart_time[vehicle_id] = depart_time

        for vehicle_id in arrived_vehicle_ids:
            self._vehicle_arrive_time[vehicle_id] = curr_time
        
        for vehicle_id in all_reachable_vehicle_ids:
            waiting_time = float(self.engine.vehicle.getParameter(vehicle_id, "device.tripinfo.waitingTime"))
            self._vehicle_waiting_time[vehicle_id] = waiting_time
            stop_count = int(self.engine.vehicle.getParameter(vehicle_id, "device.tripinfo.waitingCount"))
            self._vehicle_stop[vehicle_id] = stop_count

            # print(f"vehicle {vehicle_id} waiting time {waiting_time} stop count {stop_count}") # DEBUG

            # breakpoint()

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

        for vehicle_id in self._vehicle_arrive_time:
            if vehicle_id in self._vehicle_depart_time:
                sum_travel_time += self._vehicle_arrive_time[vehicle_id] - self._vehicle_depart_time[vehicle_id]
                effective_vehicle_num += 1

        return sum_travel_time / effective_vehicle_num if effective_vehicle_num > 0 else 0.0
    
    def get_avg_queue_length(self) -> float:
        """
        return the average queue length of all lanes
        """
        return sum(self._global_avg_queue_length) / len(self._global_avg_queue_length) if len(self._global_avg_queue_length) > 0 else 0.0
