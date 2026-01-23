from ..road_net import *
from .movement import Movement

class MovementRoadNet(RoadNet):
    """
    A road net that has movements defined. A movement is defined as a sequence of lanes that go from one edge to another.

    ### Hypothesis
        - a from-edge and a to-edge can have at most one `movement` linking them
    """

    def __init__(self, road_net: RoadNet):
        super().__init__(road_net.junction_bank, road_net.edge_bank, road_net.lane_bank, road_net.traffic_light_bank)

        self.build_movements()

    def build_movements(self):
        """
        Build movements from the road net. A movement is defined as a sequence of lanes that go from one edge to another.
        """

        movement_bank: dict[str, Movement] = {} # movement_id -> movement
        lane_movement_map: dict[str, list[Movement]] = {} # lane_id -> [movement]
        from_edge_movement_map: dict[str, list[Movement]] = {} # from_edge_id -> [movement]

        for edge in self.edges:

            edge_lane_map: dict[str, list[Lane]] = {} # to_edge_id -> [from_lane]

            for lane in edge.lanes:
                for link in lane.links:
                    to_edge_id = link.to_lane.parent_edge.id
                    if to_edge_id not in edge_lane_map:
                        edge_lane_map[to_edge_id] = []
                    edge_lane_map[to_edge_id].append(lane)
            
            for to_edge_id, from_lanes in edge_lane_map.items():
                # create movement
                movement = Movement(edge, self.get_edge(to_edge_id), from_lanes)
                movement_bank[movement.id] = movement

                # add movement to lane_movement_map
                for from_lane in from_lanes:
                    if from_lane.id not in lane_movement_map:
                        lane_movement_map[from_lane.id] = []
                    lane_movement_map[from_lane.id].append(movement)

                # add movement to from_edge_movement_map
                if edge.id not in from_edge_movement_map:
                    from_edge_movement_map[edge.id] = []
                from_edge_movement_map[edge.id].append(movement)
        
        self.movement_bank = movement_bank
        self.lane_movement_map = lane_movement_map
        self.from_edge_movement_map = from_edge_movement_map
    
    @property
    def movements(self) -> list[Movement]:
        return list(self.movement_bank.values())

    def get_movement(self, from_edge: Union[Edge, str], to_edge: Union[Edge, str], default_value = None) -> Movement:
        """
        Get the movement that goes from the given from_edge to the given to_edge.
        
        Args:
            from_edge (Union[Edge, str]): The edge to start from.
            to_edge (Union[Edge, str]): The edge to end at.
        
        Returns:
            Movement: The movement that goes from the given from_edge to the given to_edge.
        """
        if isinstance(from_edge, Edge):
            from_edge = from_edge.id
        if isinstance(to_edge, Edge):
            to_edge = to_edge.id
        return self.movement_bank.get(f'{from_edge}_{to_edge}', default_value)

    def get_movements_by_lane(self, lane: Union[Lane, str]) -> list[Movement]:
        """
        Get all movements that pass through the given lane.
        
        Args:
            lane (Union[Lane, str]): The lane to get movements for.
        
        Returns:
            list[Movement]: The movements that pass through the given lane.
        """
        if isinstance(lane, Lane):
            lane = lane.id
        if lane not in self.lane_movement_map:
            return []
        return self.lane_movement_map[lane]
    
    def get_movements_by_edge(self, edge: Union[Edge, str]) -> list[Movement]:
        """
        Get all movements that pass through the given edge.
        
        Args:
            edge (Union[Edge, str]): The edge to get movements for.
        
        Returns:
            list[Movement]: The movements that pass through the given edge.
        """
        if isinstance(edge, Edge):
            edge = edge.id
        if edge not in self.from_edge_movement_map:
            return []
        return self.from_edge_movement_map[edge]

    def get_downstream_movements(self, movement: Movement) -> list[Movement]:
        """
        Get all movements that pass through the given movement's to_edge.
        
        Args:
            movement (Movement): The movement to get downstream movements for.
        
        Returns:
            list[Movement]: The movements that pass through the given movement's to_edge.
        """
        return self.get_movements_by_edge(movement.to_edge)
    
    
    def get_upstream_movements(self, movement: Movement) -> list[Movement]:
        """
        Get all movements that pass through the given movement's from_edge.
        
        Args:
            movement (Movement): The movement to get upstream movements for.
        
        Returns:
            list[Movement]: The movements that pass through the given movement's from_edge.
        """
        from_junction = movement.from_edge.from_junction
        upstream_edges = from_junction.in_coming_edges
        upstream_movements: list[Movement] = []
        for edge in upstream_edges:
            upstream_movements.extend(self.get_movements_by_edge(edge))
        return upstream_movements