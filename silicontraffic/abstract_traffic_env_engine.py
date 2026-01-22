from abc import ABC, abstractmethod
from typing import Union, List, Callable
from .road_net import *
from .vehicle import Vehicle

class TrafficEnvEngine(ABC):
    """
    Abstract base class for traffic environment engines.
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
    def set_traffic_light_phase(self, traffic_light: Union[str, TrafficLight], phase: Union[int, TrafficLightPhase]):
        """
        Set the phase of a traffic light.

        Args:
            traffic_light (Union[str, Trafficlight]): The traffic light to set the phase for. Can be either the traffic light ID or the `Trafficlight` object.
            phase (Union[int, TrafficlightPhase]): The phase to set for the traffic light. Can be either the phase index or the `TrafficlightPhase` enum value.
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
