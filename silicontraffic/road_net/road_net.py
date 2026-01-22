from typing import Iterable, Union
from dataclasses import dataclass, field

@dataclass
class Junction:
    id: str
    position: tuple[float, float]
    shape: list = field(default_factory=list) # compatible with SUMO
    in_coming_edges: list['Edge'] = field(default_factory=list)
    out_going_edges: list['Edge'] = field(default_factory=list)
    lane_links: list['LaneLink'] = field(default_factory=list)

    @property
    def edges(self) -> list['Edge']: 
        return self.in_coming_edges + self.out_going_edges
    
    def __repr__(self) -> str:
        return f'Junction(id={self.id}, position={self.position}, num_in_coming_edges={len(self.in_coming_edges)}, num_out_going_edges={len(self.out_going_edges)}, num_lane_links={len(self.lane_links)})'
    def __str__(self) -> str:
        return self.__repr__()

@dataclass
class Edge:
    id: str
    from_junction: Junction
    to_junction: Junction
    lanes: list['Lane'] = field(default_factory=list)
    edge_type: str = ""

    @property
    def num_lanes(self) -> int:
        return len(self.lanes)
    
    def __repr__(self) -> str:
        return f'Edge(id={self.id}, from_junction={self.from_junction.id}, to_junction={self.to_junction.id}, num_lanes={self.num_lanes})'
    def __str__(self) -> str:
        return self.__repr__()

@dataclass
class Lane:
    id: str
    parent_edge: Edge
    index: int
    length: float = 0
    width: float = 0
    speed_limit: float = float('inf')
    shape: Iterable[tuple[float, float]] = field(default_factory=list)
    links: list['LaneLink'] = field(default_factory=list)
    allowed: Iterable[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f'Lane(id={self.id}, parent_edge={self.parent_edge.id}, index={self.index}, length={self.length}, width={self.width}, speed_limit={self.speed_limit})'
    def __str__(self) -> str:
        return self.__repr__()

@dataclass
class TrafficLight:
    id: str
    controlled_links: list['LaneLink']
    phases: list['TrafficLightPhase']

    def __post_init__(self):
        self._uncontrolled_links = None

    @property
    def uncontrolled_links(self) -> list['LaneLink']:
        if self._uncontrolled_links is not None:
            return self._uncontrolled_links

        result = []
        for link in self.controlled_links:
            controlled = False
            for phase in self.phases:
                if link not in phase.available_links:
                    controlled = True
                    break
            if not controlled:
                result.append(link)

        # for phase in self.phases:
        #     print('phase', phase.index)
        #     for link in phase.available_links:
        #         print(f'{link.from_lane.id} -> {link.to_lane.id}')
        #     print()

        self._uncontrolled_links = result
        return result
    
    def __repr__(self) -> str:
        return f'TrafficLight(id={self.id}, num_controlled_links={len(self.controlled_links)}, num_phases={len(self.phases)})'
    def __str__(self) -> str:
        return self.__repr__()

@dataclass
class LaneLink:
    from_lane: Lane
    to_lane: Lane
    link_lane: Lane
    type: Union[str, None] = None

    def __eq__(self, other: 'LaneLink') -> bool:
        return (self.from_lane.id == other.from_lane.id and self.to_lane.id == other.to_lane.id)
    
    def __repr__(self) -> str:
        return f'LaneLink(from_lane={self.from_lane.id}, to_lane={self.to_lane.id}, link_lane={self.link_lane.id}, type={self.type})'
    def __str__(self) -> str:
        return self.__repr__()

@dataclass
class TrafficLightPhase:
    index: int
    duration: float
    parent_trafficlight: TrafficLight
    available_links: list[LaneLink]

    def __post_init__(self):
        self.id = f'{self.parent_trafficlight.id}_phase_{self.index}'
    
    def __repr__(self) -> str:
        return f'TrafficLightPhase(id={self.id}, duration={self.duration}, num_available_links={len(self.available_links)})'
    def __str__(self) -> str:
        return self.__repr__()

@dataclass
class RoadNet:
    junction_bank: dict[str, Junction] = field(default_factory=dict)
    edge_bank: dict[str, Edge] = field(default_factory=dict)
    lane_bank: dict[str, Lane] = field(default_factory=dict)
    traffic_light_bank: dict[str, TrafficLight] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f'RoadNet({len(self.junction_bank)} junctions, {len(self.edge_bank)} edges, {len(self.lane_bank)} lanes, {len(self.traffic_light_bank)} traffic lights)'

    def __str__(self) -> str:
        return self.__repr__()
    
    def get_junction(self, id: str, default_value = None) -> Junction:
        return self.junction_bank.get(id, default_value)
    
    def get_edge(self, id: str, default_value = None) -> Edge:
        return self.edge_bank.get(id, default_value)
    
    def get_lane(self, id: str, default_value = None) -> Lane:
        return self.lane_bank.get(id, default_value)
    
    def get_traffic_light(self, id: str, default_value = None) -> TrafficLight:
        return self.traffic_light_bank.get(id, default_value)
    
    @property
    def junctions(self) -> list[Junction]:
        return list(self.junction_bank.values())
    
    @property
    def edges(self) -> list[Edge]:
        return list(self.edge_bank.values())
    
    @property
    def lanes(self) -> list[Lane]:
        return list(self.lane_bank.values())
    
    @property
    def traffic_lights(self) -> list[TrafficLight]:
        return list(self.traffic_light_bank.values())
