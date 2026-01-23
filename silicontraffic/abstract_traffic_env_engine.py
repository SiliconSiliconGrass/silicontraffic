from abc import ABC, abstractmethod
from typing import Union, List, Callable
from .road_net import *
from .vehicle import Vehicle

class TrafficEnvEngine(ABC):
    """
    Abstract base class for traffic environment engines.

    ### provides:
        - `road_net` attribute, to ensure convenient access to road net structure info.
        - `get_time` method, to get the current simulation time.
        - `get_lane_vehicle_ids` method, to get the IDs of vehicles on a lane.
        - `get_vehicle_info` method, to get the information of a vehicle.
        - `get_traffic_light_phase` method, to get the phase of a traffic light.
        - `set_traffic_light_phase` method, to set the phase of a traffic light.
    
    ### Note that `TrafficEnvEngine` instances only provide basic traffic data retrieval methods, for advanced statistics, see `silicontraffic.monitor` module
    """

    road_net: RoadNet
    """`TrafficEnvEngine` instances should provide `road_net` attribute, to ensure convenient access to road net structure info."""

    def __init__(self):
        self.step_handlers: List[Callable[['TrafficEnvEngine'], None]] = []

    @abstractmethod
    def reset(self):
        """
        Reset the traffic environment to its initial state.
        """
        pass

    @abstractmethod
    def terminate(self):
        """
        Terminate the traffic environment simulation.
        """
        pass

    @abstractmethod
    def _simulation_step(self, step_num: int = 1):
        """
        Perform a simulation step.

        Args:
            step_num (int, optional): The number of steps to simulate. Defaults to 1.
        """
        pass

    @abstractmethod
    def get_time(self) -> float:
        """
        Get the current simulation time.

        Returns:
            float: The current simulation time.
        """
        pass
    
    @abstractmethod
    def get_lane_vehicle_ids(self, lane: Union[str, Lane]) -> list[str]:
        """
        Get the IDs of vehicles on a lane.

        Args:
            lane (Union[str, Lane]): The lane to get the vehicle IDs for. Can be either the lane ID or the `Lane` object.

        Returns:
            list[str]: The IDs of vehicles on the lane.
        """
        pass

    @abstractmethod
    def get_vehicle_info(self, vehicle_id) -> Vehicle:
        """
        Get the information of a vehicle.

        Args:
            vehicle_id (str): The ID of the vehicle.

        Returns:
            Vehicle: The information of the vehicle.
        """
        pass

    @abstractmethod
    def get_traffic_light_phase(self, traffic_light: Union[str, TrafficLight]) -> TrafficLightPhase:
        """
        Get the phase of a traffic light.

        Args:
            traffic_light (Union[str, TrafficLight]): The traffic light to get the phase for. Can be either the traffic light ID or the `TrafficLight` object.

        Returns:
            TrafficLightPhase: The phase of the traffic light.
        """
        pass

    @abstractmethod
    def set_traffic_light_phase(self, traffic_light: Union[str, TrafficLight], phase: Union[int, TrafficLightPhase]):
        """
        Set the phase of a traffic light.

        Args:
            traffic_light (Union[str, TrafficLight]): The traffic light to set the phase for. Can be either the traffic light ID or the `TrafficLight` object.
            phase (Union[int, TrafficLightPhase]): The phase to set for the traffic light. Can be either the phase index or the `TrafficLightPhase` enum value.
        """
        pass


    def step(self, step_num: int = 1):
        """
        Perform multiple simulation steps.

        Args:
            step_num (int, optional): The number of steps to simulate. Defaults to 1.
        """
        if len(self.step_handlers) > 0:
            for _ in range(step_num):
                self._simulation_step()
                for handler in self.step_handlers:
                    handler(self)
        else:
            self._simulation_step(step_num) # be more efficient when no step handlers registered
    
    def on_step(self, handler: Callable[['TrafficEnvEngine'], None]):
        """
        Register a step handler function.

        Args:
            handler (Callable[['TrafficEnvEngine'], None]): The step handler function to register.
        
        Examples:
        ```
            @my_env.on_step
            def my_step_handler(traffic_env_engine: TrafficEnvEngine):
                # do something with traffic_env_engine
                pass
        ```
            or
        ```
            my_env.on_step(my_step_handler)
        ```
        """
        self.step_handlers.append(handler)
        return handler

    def get_lane_queue_length(self, lane: Union[str, Lane], speed_threshold: float = 0.1) -> int:
        """
        Get the queue length of a lane.

        Args:
            lane (Union[str, Lane]): The lane to get the queue length for. Can be either the lane ID or the `Lane` object.
            speed_threshold (float, optional): The speed threshold to consider a vehicle as in queue. Defaults to 0.1.

        Returns:
            int: The queue length of the lane. (the number of vehicles with speed less than `speed_threshold`)
        """
        vehicle_ids = self.get_lane_vehicle_ids(lane)
        queue_length = 0
        for vehicle_id in vehicle_ids:
            vehicle = self.get_vehicle_info(vehicle_id)
            if vehicle.speed < speed_threshold:
                queue_length += 1
        return queue_length