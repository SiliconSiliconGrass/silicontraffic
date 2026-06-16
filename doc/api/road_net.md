# 道路网络 API

## 概述

道路网络模块提供了统一的道路网络数据模型，包括路口、路段、车道、交通灯等核心组件。

## 核心数据结构

### Junction（路口）

```python
@dataclass
class Junction:
    id: str
    position: tuple[float, float]
    shape: list = field(default_factory=list)
    in_coming_edges: list['Edge'] = field(default_factory=list)
    out_going_edges: list['Edge'] = field(default_factory=list)
    lane_links: list['LaneLink'] = field(default_factory=list)
    
    @property
    def edges(self) -> list['Edge']:
        """返回所有关联的路段"""
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | str | 路口唯一标识 |
| `position` | tuple[float, float] | 路口坐标位置 |
| `shape` | list | 路口形状（SUMO兼容） |
| `in_coming_edges` | list[Edge] | 入路段列表 |
| `out_going_edges` | list[Edge] | 出路段列表 |
| `lane_links` | list[LaneLink] | 车道连接列表 |

### Edge（路段）

```python
@dataclass
class Edge:
    id: str
    from_junction: Junction
    to_junction: Junction
    lanes: list['Lane'] = field(default_factory=list)
    edge_type: str = ""
    
    @property
    def num_lanes(self) -> int:
        """返回车道数量"""
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | str | 路段唯一标识 |
| `from_junction` | Junction | 起始路口 |
| `to_junction` | Junction | 终止路口 |
| `lanes` | list[Lane] | 车道列表 |
| `edge_type` | str | 路段类型 |

### Lane（车道）

```python
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
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | str | 车道唯一标识 |
| `parent_edge` | Edge | 所属路段 |
| `index` | int | 车道索引 |
| `length` | float | 车道长度（米） |
| `width` | float | 车道宽度（米） |
| `speed_limit` | float | 限速（米/秒） |
| `shape` | Iterable | 车道形状坐标 |
| `links` | list[LaneLink] | 车道连接列表 |
| `allowed` | Iterable[str] | 允许的车辆类型 |

### LaneLink（车道连接）

```python
@dataclass
class LaneLink:
    from_lane: Lane
    to_lane: Lane
    link_lane: Lane
    type: Union[str, None] = None
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `from_lane` | Lane | 起始车道 |
| `to_lane` | Lane | 目标车道 |
| `link_lane` | Lane | 连接车道 |
| `type` | str | 连接类型 |

### TrafficLight（交通灯）

```python
@dataclass
class TrafficLight:
    id: str
    controlled_links: list['LaneLink']
    phases: list['TrafficLightPhase']
    
    @property
    def uncontrolled_links(self) -> list['LaneLink']:
        """返回不受控制的连接"""
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | str | 交通灯唯一标识 |
| `controlled_links` | list[LaneLink] | 控制的车道连接 |
| `phases` | list[TrafficLightPhase] | 相位列表 |

### TrafficLightPhase（交通灯相位）

```python
@dataclass
class TrafficLightPhase:
    index: int
    duration: float
    parent_trafficlight: TrafficLight
    available_links: list[LaneLink]
    
    def __post_init__(self):
        self.id = f'{self.parent_trafficlight.id}_phase_{self.index}'
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `index` | int | 相位索引 |
| `duration` | float | 相位持续时间 |
| `parent_trafficlight` | TrafficLight | 所属交通灯 |
| `available_links` | list[LaneLink] | 允许通行的车道连接 |

---

## RoadNet（道路网络）

### 类定义

```python
@dataclass
class RoadNet:
    junction_bank: dict[str, Junction] = field(default_factory=dict)
    edge_bank: dict[str, Edge] = field(default_factory=dict)
    lane_bank: dict[str, Lane] = field(default_factory=dict)
    traffic_light_bank: dict[str, TrafficLight] = field(default_factory=dict)
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `junction_bank` | dict[str, Junction] | 路口字典 |
| `edge_bank` | dict[str, Edge] | 路段字典 |
| `lane_bank` | dict[str, Lane] | 车道字典 |
| `traffic_light_bank` | dict[str, TrafficLight] | 交通灯字典 |

### 属性（只读）

| 属性 | 类型 | 说明 |
|------|------|------|
| `junctions` | list[Junction] | 所有路口列表 |
| `edges` | list[Edge] | 所有路段列表 |
| `lanes` | list[Lane] | 所有车道列表 |
| `traffic_lights` | list[TrafficLight] | 所有交通灯列表 |

### 方法

#### get_junction(id, default_value=None) -> Junction

```python
def get_junction(self, id: str, default_value = None) -> Junction:
    """
    获取路口对象。
    
    Args:
        id: 路口ID
        default_value: 默认返回值
        
    Returns:
        Junction: 路口对象
    """
```

#### get_edge(id, default_value=None) -> Edge

```python
def get_edge(self, id: str, default_value = None) -> Edge:
    """
    获取路段对象。
    
    Args:
        id: 路段ID
        default_value: 默认返回值
        
    Returns:
        Edge: 路段对象
    """
```

#### get_lane(id, default_value=None) -> Lane

```python
def get_lane(self, id: str, default_value = None) -> Lane:
    """
    获取车道对象。
    
    Args:
        id: 车道ID
        default_value: 默认返回值
        
    Returns:
        Lane: 车道对象
    """
```

#### get_traffic_light(id, default_value=None) -> TrafficLight

```python
def get_traffic_light(self, id: str, default_value = None) -> TrafficLight:
    """
    获取交通灯对象。
    
    Args:
        id: 交通灯ID
        default_value: 默认返回值
        
    Returns:
        TrafficLight: 交通灯对象
    """
```

---

## 加载道路网络

### 加载 SUMO 道路网络

```python
from silicontraffic.ssumo import load_sumo_road_net

# 从 SUMO 网络文件加载
road_net = load_sumo_road_net("path/to/network.net.xml")

# 从引擎获取（推荐）
from silicontraffic import SiliconSumoEngine
engine = SiliconSumoEngine("path/to/config.sumocfg")
road_net = engine.road_net
```

### 加载 CityFlow 道路网络

```python
from silicontraffic.scityflow import load_cityflow_road_net

# 从 CityFlow 道路网络文件加载
road_net = load_cityflow_road_net("path/to/roadnet.json")

# 从引擎获取（推荐）
from silicontraffic import SiliconCityFlowEngine
engine = SiliconCityFlowEngine("path/to/cityflow.config")
road_net = engine.road_net
```

---

## 使用示例

### 遍历道路网络

```python
from silicontraffic import SiliconSumoEngine

engine = SiliconSumoEngine("config.sumocfg")
road_net = engine.road_net

# 遍历所有路口
print(f"路口数量: {len(road_net.junctions)}")
for junction in road_net.junctions:
    print(f"路口 {junction.id}: {len(junction.in_coming_edges)} 入路段, {len(junction.out_going_edges)} 出路段")

# 遍历所有路段
print(f"\n路段数量: {len(road_net.edges)}")
for edge in road_net.edges:
    print(f"路段 {edge.id}: {edge.from_junction.id} -> {edge.to_junction.id}, {edge.num_lanes} 车道")

# 遍历所有交通灯
print(f"\n交通灯数量: {len(road_net.traffic_lights)}")
for tl in road_net.traffic_lights:
    print(f"交通灯 {tl.id}: {len(tl.phases)} 个相位")
    for phase in tl.phases:
        print(f"  相位 {phase.index}: {len(phase.available_links)} 条允许连接")
```

### 获取特定元素

```python
# 获取特定路口
junction = road_net.get_junction("junction_0")

# 获取特定路段
edge = road_net.get_edge("edge_0")

# 获取特定车道
lane = road_net.get_lane("edge_0_0")

# 获取特定交通灯
tl = road_net.get_traffic_light("tl_0")

# 获取交通灯的所有相位
phases = tl.phases
for phase in phases:
    print(f"相位 {phase.index}: 持续时间 {phase.duration}s")
```

### 分析车道连接

```python
# 获取车道的所有连接
lane = road_net.get_lane("edge_0_0")
for link in lane.links:
    print(f"车道 {lane.id} 连接到 {link.to_lane.id}")

# 获取交通灯控制的连接
tl = road_net.get_traffic_light("tl_0")
for link in tl.controlled_links:
    print(f"交通灯 {tl.id} 控制: {link.from_lane.id} -> {link.to_lane.id}")
```
