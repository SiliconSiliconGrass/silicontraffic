from __future__ import annotations

from typing import Iterable, Optional, TypeVar, Union
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

    @property
    def incoming_lanes(self) -> list['Lane']:
        return [lane for edge in self.in_coming_edges for lane in edge.lanes]

    @property
    def outgoing_lanes(self) -> list['Lane']:
        return [lane for edge in self.out_going_edges for lane in edge.lanes]
    
    def __repr__(self) -> str:
        return f'Junction(id={self.id}, position={self.position}, num_in_coming_edges={len(self.in_coming_edges)}, num_out_going_edges={len(self.out_going_edges)}, num_lane_links={len(self.lane_links)})'
    def __str__(self) -> str:
        return self.__repr__()
    def __hash__(self):
        return hash(self.id)

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
        from_junction_id = self.from_junction.id if self.from_junction is not None else None
        to_junction_id = self.to_junction.id if self.to_junction is not None else None
        return f'Edge(id={self.id}, from_junction={from_junction_id}, to_junction={to_junction_id}, num_lanes={self.num_lanes})'
    def __str__(self) -> str:
        return self.__repr__()
    def __hash__(self):
        return hash(self.id)

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
    incoming_links: list['LaneLink'] = field(default_factory=list)
    allowed: Iterable[str] = field(default_factory=list)

    @property
    def from_junction(self) -> Junction:
        return self.parent_edge.from_junction

    @property
    def to_junction(self) -> Junction:
        return self.parent_edge.to_junction

    @property
    def outgoing_lanes(self) -> list['Lane']:
        return [link.to_lane for link in self.links]

    @property
    def incoming_lanes(self) -> list['Lane']:
        return [link.from_lane for link in self.incoming_links]

    @property
    def upstream_lanes(self) -> list['Lane']:
        """Alias of `incoming_lanes`: lanes directly upstream of this lane."""
        return self.incoming_lanes

    @property
    def downstream_lanes(self) -> list['Lane']:
        """Alias of `outgoing_lanes`: lanes directly downstream of this lane."""
        return self.outgoing_lanes

    def __repr__(self) -> str:
        parent_edge_id = self.parent_edge.id if self.parent_edge is not None else None
        return f'Lane(id={self.id}, parent_edge={parent_edge_id}, index={self.index}, length={self.length}, width={self.width}, speed_limit={self.speed_limit})'
    def __str__(self) -> str:
        return self.__repr__()
    def __hash__(self):
        return hash(self.id)
    def __eq__(self, other: 'Lane'):
        return self.id == other.id


@dataclass
class ExtendedLane:
    """
    An approach "extended" beyond the lane that directly ends at a signal
    junction, through upstream (usually degree-2 / lane-count-change)
    junctions. `lanes` is ordered head-first (the lane at the stop line is
    `head_lane`); queue / waiting statistics of the extended lane are the
    aggregated statistics of every constituent lane.
    """
    head_lane: Lane
    lanes: tuple[Lane, ...]
    length: float
    outgoing: list['LaneLike'] = field(default_factory=list)

    def __post_init__(self):
        self.id = f'{self.head_lane.id}__ext'

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other) -> bool:
        return isinstance(other, ExtendedLane) and self.id == other.id

    def __repr__(self) -> str:
        return f'ExtendedLane(id={self.id}, num_lanes={len(self.lanes)}, length={self.length})'
    def __str__(self) -> str:
        return self.__repr__()


LaneLike = TypeVar("LaneLike", bound=Union[Lane, ExtendedLane])

@dataclass
class TrafficLight:
    id: str
    controlled_links: list['LaneLink']
    phases: list['TrafficLightPhase']
    junctions: set[Junction] = field(default_factory=set)
    controlled_links_extended: list['LaneLink'] = field(default_factory=list)

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
    def __hash__(self):
        return hash(self.id)

@dataclass
class LaneLink:
    from_lane: LaneLike
    to_lane: LaneLike
    link_lane: LaneLike
    type: Union[str, None] = None

    def __eq__(self, other: 'LaneLink') -> bool:
        return (self.from_lane.id == other.from_lane.id and self.to_lane.id == other.to_lane.id)
    
    def __repr__(self) -> str:
        from_lane_id = self.from_lane.id if self.from_lane is not None else None
        to_lane_id = self.to_lane.id if self.to_lane is not None else None
        link_lane_id = self.link_lane.id if self.link_lane is not None else None
        return f'LaneLink(from_lane={from_lane_id}, to_lane={to_lane_id}, link_lane={link_lane_id}, type={self.type})'
    def __str__(self) -> str:
        return self.__repr__()
    def __hash__(self):
        return hash((self.from_lane.id, self.to_lane.id))

@dataclass
class TrafficLightPhase:
    index: int
    duration: float
    parent_trafficlight: TrafficLight
    available_links: list[LaneLink]
    available_links_extended: list[LaneLink] = field(default_factory=list)

    def __post_init__(self):
        self.id = f'{self.parent_trafficlight.id}_phase_{self.index}'
    
    def __repr__(self) -> str:
        return f'TrafficLightPhase(id={self.id}, duration={self.duration}, num_available_links={len(self.available_links)})'
    def __str__(self) -> str:
        return self.__repr__()
    def __hash__(self):
        return hash(self.id)

@dataclass
class RoadNet:
    junction_bank: dict[str, Junction] = field(default_factory=dict)
    edge_bank: dict[str, Edge] = field(default_factory=dict)
    lane_bank: dict[str, Lane] = field(default_factory=dict)
    traffic_light_bank: dict[str, TrafficLight] = field(default_factory=dict)
    extended_lane_bank: dict[str, ExtendedLane] = field(default_factory=dict)
    """ head lane id -> ExtendedLane """
    incoming_lane_map: dict[str, LaneLike] = field(default_factory=dict)
    """ lane id -> ExtendedLane (or the plain Lane when not extended) """
    outgoing_lane_map: dict[str, LaneLike] = field(default_factory=dict)
    """ lane id -> ExtendedLane (or the plain Lane) used as this lane's outgoing """
    outgoing_map: dict[str, list[LaneLike]] = field(default_factory=dict)
    """ lane id / extended lane id -> list of outgoing LaneLike """
    outgoing_extended_lane_bank: dict[str, 'ExtendedLane'] = field(default_factory=dict)
    """ outgoing (downstream) head lane id -> ExtendedLane """
    extended_lane_max_distance: Optional[float] = None
    """ distance cap used when the extended lanes were built (None = no cap) """

    def __post_init__(self):
        self._junction_tl_map: dict[str, TrafficLight] = {}
        for tl in self.traffic_lights:
            for junction in tl.junctions:
                self._junction_tl_map[junction.id] = tl

    def __repr__(self) -> str:
        return f'RoadNet(num_junctions={len(self.junction_bank)}, num_edges={len(self.edge_bank)}, num_lanes={len(self.lane_bank)}, num_traffic_lights={len(self.traffic_light_bank)})'

    def __str__(self) -> str:
        return self.__repr__()
    def __hash__(self):
        return hash(id(self))
    
    def get_junction(self, id: str, default_value = None) -> Junction:
        return self.junction_bank.get(id, default_value)
    
    def get_edge(self, id: str, default_value = None) -> Edge:
        return self.edge_bank.get(id, default_value)
    
    def get_lane(self, id: str, default_value = None) -> Lane:
        return self.lane_bank.get(id, default_value)
    
    def get_traffic_light(self, id: str, default_value = None) -> TrafficLight:
        return self.traffic_light_bank.get(id, default_value)

    def get_traffic_light_by_junction(self, junction: Union[str, Junction], default_value = None) -> TrafficLight:
        """
        Get the traffic light that controls the given junction.

        Args:
            junction (str | Junction): the junction (or its ID).

        Returns:
            TrafficLight | None: the controlling traffic light, or `default_value`
            if the junction is not signalized.
        """
        junction_id = junction.id if isinstance(junction, Junction) else junction
        return self._junction_tl_map.get(junction_id, default_value)

    def get_outgoings(self, lane_like: LaneLike) -> list[LaneLike]:
        """
        Get the outgoing lanes (or extended outgoing lanes) of a lane /
        extended lane. Returns an empty list if the lane is not an approach
        of a signalized junction and no mapping was built.
        """
        if isinstance(lane_like, ExtendedLane):
            return lane_like.outgoing
        if lane_like.id in self.outgoing_map:
            return self.outgoing_map[lane_like.id]
        return [
            self.outgoing_lane_map.get(link.to_lane.id, link.to_lane)
            for link in lane_like.links
        ]
    
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
