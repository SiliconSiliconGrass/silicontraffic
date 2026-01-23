try:
    import traci
except (ImportError, ModuleNotFoundError):
    raise ImportError("traci module not found. Please install sumo first.")
try:
    import sumolib
except (ImportError, ModuleNotFoundError):
    raise ImportError("sumolib module not found. Please install sumo first.")

import os
import subprocess
import random
import time
import xml.etree.ElementTree as ET

from sumolib import checkBinary as check_binary

# Import these domain classes for type hint purpose
from traci._busstop import BusStopDomain
from traci._calibrator import CalibratorDomain
from traci._chargingstation import ChargingStationDomain
from traci._edge import EdgeDomain
from traci._gui import GuiDomain
from traci._inductionloop import InductionLoopDomain
from traci._junction import JunctionDomain
from traci._lane import LaneDomain
from traci._lanearea import LaneAreaDomain
from traci._meandata import MeanDataDomain
from traci._multientryexit import MultiEntryExitDomain
from traci._overheadwire import OverheadWireDomain
from traci._parkingarea import ParkingAreaDomain
from traci._person import PersonDomain
from traci._poi import PoiDomain
from traci._polygon import PolygonDomain
from traci._rerouter import RerouterDomain
from traci._route import RouteDomain
from traci._routeprobe import RouteProbeDomain
from traci._simulation import SimulationDomain
from traci._trafficlight import TrafficLightDomain
from traci._variablespeedsign import VariableSpeedSignDomain
from traci._vehicle import VehicleDomain
from traci._vehicletype import VehicleTypeDomain

from typing import Callable, Union

from .sumo_road_net import load_sumo_road_net
from .get_unique_port import get_unique_port
from ..abstract_traffic_env_engine import TrafficEnvEngine
from ..road_net import *
from ..vehicle import Vehicle

SUMO = check_binary('sumo')
SUMO_GUI = check_binary('sumo-gui')

class SiliconSumoEngine(TrafficEnvEngine):
    def __init__(self, sumocfg_path: str, log_path: str = "temp/", port: int = None, seed: int = None, time_to_teleport: int = 600, waiting_time_memory: int = 100, use_gui: bool = False):
        super().__init__()
        self.sumocfg_path = sumocfg_path

        if seed is None:
            seed = random.randint(0, 1000000)
        self.seed = seed

        if port is None:
            port = get_unique_port()
        self.port = port

        self.log_path = log_path
        self.time_to_teleport = time_to_teleport
        self.waiting_time_memory = waiting_time_memory
        self.use_gui = use_gui
        
        self._connection: traci.connection.Connection = None

        # Load road net
        self.road_net: RoadNet = None
        self.update_road_net()
        self.traffic_light_ids = list(self.road_net.traffic_light_bank.keys())

        # Create domain instances as exposed APIs (exactly the same usage with traci)
        self.busstop = BusStopDomain()
        self.calibrator = CalibratorDomain()
        self.chargingstation = ChargingStationDomain()
        self.edge = EdgeDomain()
        self.gui = GuiDomain()
        self.inductionloop = InductionLoopDomain()
        self.junction = JunctionDomain()
        self.lane = LaneDomain()
        self.lanearea = LaneAreaDomain()
        self.meandata = MeanDataDomain()
        self.multientryexit = MultiEntryExitDomain()
        self.overheadwire = OverheadWireDomain()
        self.parkingarea = ParkingAreaDomain()
        self.person = PersonDomain()
        self.poi = PoiDomain()
        self.polygon = PolygonDomain()
        self.rerouter = RerouterDomain()
        self.route = RouteDomain()
        self.routeprobe = RouteProbeDomain()
        self.simulation = SimulationDomain()
        self.trafficlight = TrafficLightDomain()
        self.variablespeedsign = VariableSpeedSignDomain()
        self.vehicle = VehicleDomain()
        self.vehicletype = VehicleTypeDomain()

        self._cache_lane_vehicle_ids: dict[str, list[str]] = {} # lane id -> list of vehicle ids
        self._cache_vehicle_info: dict[str, Vehicle] = {} # vehicle id -> vehicle
    
    def update_road_net(self):
        # Parse sumocfg to get net-file path
        self.net_file_path = None
        tree = ET.parse(self.sumocfg_path)
        root = tree.getroot()
        for elem in root.iter():
            if 'net-file' == elem.tag:
                self.net_file_path = elem.get('value')
                break
        
        assert self.net_file_path is not None, "`net-file` tag not found in sumocfg"

        # Load road net
        self.road_net = load_sumo_road_net(os.path.join(os.path.dirname(self.sumocfg_path), self.net_file_path))

    def terminate(self):
        if self._connection:
            self._connection.close()
    
    def reset(self):
        if self._connection:
            self.terminate()

        binary = SUMO_GUI if self.use_gui else SUMO

        command = [binary, '-c', self.sumocfg_path]
        command += ['--seed', str(self.seed)]
        command += ['--remote-port', str(self.port)]
        command += ['--no-step-log', 'True']
        command += ['--time-to-teleport', str(self.time_to_teleport)]
        command += ['--no-warnings', 'True']
        command += ['--duration-log.disable', 'True']
        # command += ['--waiting-time-memory', str(self.waiting_time_memory)]
        command += ['--tripinfo-output', os.path.join(self.log_path, 'trip.xml')]
        subprocess.Popen(command)

        time.sleep(1) # wait for sumo to start

        self._connection = traci.connect(port=self.port)
        
        # Set connections for domain instances, so that they can be used as exposed APIs
        self.busstop._setConnection(self._connection)
        self.calibrator._setConnection(self._connection)
        self.chargingstation._setConnection(self._connection)
        self.edge._setConnection(self._connection)
        self.gui._setConnection(self._connection)
        self.inductionloop._setConnection(self._connection)
        self.junction._setConnection(self._connection)
        self.lane._setConnection(self._connection)
        self.lanearea._setConnection(self._connection)
        self.meandata._setConnection(self._connection)
        self.multientryexit._setConnection(self._connection)
        self.overheadwire._setConnection(self._connection)
        self.parkingarea._setConnection(self._connection)
        self.person._setConnection(self._connection)
        self.poi._setConnection(self._connection)
        self.polygon._setConnection(self._connection)
        self.rerouter._setConnection(self._connection)
        self.route._setConnection(self._connection)
        self.routeprobe._setConnection(self._connection)
        self.simulation._setConnection(self._connection)
        self.trafficlight._setConnection(self._connection)
        self.variablespeedsign._setConnection(self._connection)
        self.vehicle._setConnection(self._connection)
        self.vehicletype._setConnection(self._connection)

        self._cache_lane_vehicle_ids.clear()
        self._cache_vehicle_info.clear()

    def _simulation_step(self, step_num: int = 1):
        self._cache_lane_vehicle_ids.clear()
        self._cache_vehicle_info.clear()
        if step_num < 1:
            step_num = 1
        for _ in range(int(step_num)):
            self._connection.simulationStep()
    
    def get_time(self) -> float:
        return self.simulation.getTime()
    
    def set_traffic_light_phase(self, traffic_light: Union[str, TrafficLight], phase: Union[int, TrafficLightPhase]):
        if isinstance(traffic_light, TrafficLight):
            traffic_light = traffic_light.id
        if isinstance(phase, TrafficLightPhase):
            phase = phase.index
        self.trafficlight.setPhase(traffic_light, phase)
    
    def get_traffic_light_phase(self, traffic_light: Union[str, TrafficLight]) -> TrafficLightPhase:
        if isinstance(traffic_light, TrafficLight):
            traffic_light = traffic_light.id
        assert traffic_light in self.traffic_light_ids, f"traffic light {traffic_light} not found"
        phase_index = self.trafficlight.getPhase(traffic_light)
        return self.road_net.get_traffic_light(traffic_light).phases[phase_index]
    
    def get_lane_vehicle_ids(self, lane: Union[str, Lane]) -> list[str]:
        if isinstance(lane, Lane):
            lane = lane.id
        if lane in self._cache_lane_vehicle_ids:
            return self._cache_lane_vehicle_ids[lane]
        self._cache_lane_vehicle_ids[lane] = self.lane.getLastStepVehicleIDs(lane)
        return self._cache_lane_vehicle_ids[lane]
    
    def get_vehicle_info(self, vehicle_id) -> Vehicle:
        if vehicle_id in self._cache_vehicle_info:
            return self._cache_vehicle_info[vehicle_id]

        running = (self.vehicle.getRouteIndex(vehicle_id) != -1)

        if not running:
            vehicle = Vehicle(vehicle_id, running=False)

        else:
            lane_position = self.vehicle.getLanePosition(vehicle_id)
            speed = self.vehicle.getSpeed(vehicle_id)
            drivable_id = self.vehicle.getLaneID(vehicle_id)
            route = self.vehicle.getRoute(vehicle_id)
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
    
    # def get_lane_queue_length(self, lane: Union[str, Lane], speed_threshold = None) -> int:
    #     if isinstance(lane, Lane):
    #         lane = lane.id
    #     return self.lane.getLastStepHaltingNumber(lane)