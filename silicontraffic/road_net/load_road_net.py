from os import PathLike
from typing import Literal
from .road_net import RoadNet
from ..ssumo import load_sumo_road_net
from ..scityflow import load_cityflow_road_net

def load_road_net(engine_type: Literal["sumo", "cityflow"], road_net_file_path: PathLike) -> RoadNet:
    if engine_type == "sumo":
        return load_sumo_road_net(road_net_file_path)
    elif engine_type == "cityflow":
        return load_cityflow_road_net(road_net_file_path)
    else:
        raise ValueError(f"Unknown engine type: {engine_type}")
