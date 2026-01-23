from dataclasses import dataclass
from ..road_net import *

@dataclass
class Movement:
    from_edge: Edge
    to_edge: Edge
    from_lanes: list[Lane]

    def __post_init__(self):
        self.id = f'{self.from_edge.id}_{self.to_edge.id}'
    
    def __repr__(self) -> str:
        return f'Movement(from_edge={self.from_edge.id}, to_edge={self.to_edge.id}, num_from_lanes={len(self.from_lanes)})'
    def __str__(self) -> str:
        return self.__repr__()
