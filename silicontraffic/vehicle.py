from dataclasses import dataclass, field

@dataclass
class Vehicle:
    id: str

    lane_position: float = None
    """The distance vehicle has traveled along current lane."""

    speed: float = None
    drivable_id: str = None
    vehicle_type: str = None
    route: list[str] = field(default_factory=list) # a list of edge ids

    def __repr__(self) -> str:
        return f'Vehicle(id={self.id}, lane_position={self.lane_position}, speed={self.speed}, drivable_id={self.drivable_id}, vehicle_type={self.vehicle_type}, route={self.route})'
    def __str__(self) -> str:
        return self.__repr__()