from abc import ABC, abstractmethod
from ..abstract_traffic_env_engine import TrafficEngine

class Monitor(ABC):
    """
    Abstract base class for traffic monitors.
    """
    def __init__(self):
        self._auto_reset = False

    @abstractmethod
    def attach_to(self, engine: TrafficEngine):
        pass

    @abstractmethod
    def reset(self):
        """
        Reset the monitor.
        """
        pass
    
    def setup_auto_reset(self, engine: TrafficEngine):
        """
        Setup auto reset function, so that the monitor will reset automatically when engine is reset.
        """
        # check if auto reset is already setup
        if self._auto_reset:
            raise RuntimeError("Auto reset is already setup. Are you attaching the monitor to multiple engines? Or mistakenly setup auto reset multiple times?")

        self._auto_reset = True
        self._auto_reset_prev_recorded_time = None

        @engine.on_step
        def _reset_monitor(_: TrafficEngine):
            curr_time = engine.get_time()
            if self._auto_reset_prev_recorded_time is not None and curr_time < self._auto_reset_prev_recorded_time: # reset when time is smaller than the last recorded time
                self.reset()
            self._auto_reset_prev_recorded_time = curr_time
