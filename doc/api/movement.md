# 运动建模 API

## 概述

运动建模模块提供了基于路段的交通运动分析功能，支持定义和查询交通运动。

## Movement（运动）

### 类定义

```python
@dataclass
class Movement:
    from_edge: Edge
    to_edge: Edge
    from_lanes: list[Lane]
    traffic_light: Optional[TrafficLight] = None
    
    def __post_init__(self):
        self.id = f'{self.from_edge.id}_{self.to_edge.id}'
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `from_edge` | Edge | 起始路段 |
| `to_edge` | Edge | 目标路段 |
| `from_lanes` | list[Lane] | 起始车道列表 |
| `traffic_light` | Optional[TrafficLight] | 控制此运动的交通灯 |
| `id` | str | 运动唯一标识（自动生成） |

### 示例

```python
movement = Movement(
    from_edge=edge1,
    to_edge=edge2,
    from_lanes=[lane1, lane2],
    traffic_light=tl
)
print(f"运动ID: {movement.id}")
print(f"起始路段: {movement.from_edge.id}")
print(f"目标路段: {movement.to_edge.id}")
```

---

## MovementRoadNet（运动道路网络）

### 类定义

```python
class MovementRoadNet(RoadNet):
    """
    具有运动定义的道路网络。运动定义为从一个路段到另一个路段的车道序列。
    
    假设：
        - 一个起始路段和一个目标路段之间最多有一个运动连接
    """
```

### 构造函数

```python
def __init__(self, road_net: RoadNet):
    """
    Args:
        road_net: 基础道路网络对象
    """
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `movement_bank` | dict[str, Movement] | 运动字典 |
| `lane_movement_map` | dict[str, list[Movement]] | 车道-运动映射 |
| `from_edge_movement_map` | dict[str, list[Movement]] | 起始路段-运动映射 |
| `traffic_light_movement_map` | dict[str, list[Movement]] | 交通灯-运动映射 |
| `phase_movement_map` | dict[str, list[Movement]] | 相位-运动映射 |

### 属性（只读）

| 属性 | 类型 | 说明 |
|------|------|------|
| `movements` | list[Movement] | 所有运动列表 |

### 方法详解

#### get_movement(from_edge, to_edge, default_value=None) -> Movement

```python
def get_movement(self, from_edge: Union[Edge, str], to_edge: Union[Edge, str], 
                 default_value = None) -> Movement:
    """
    获取从起始路段到目标路段的运动。
    
    Args:
        from_edge: 起始路段或路段ID
        to_edge: 目标路段或路段ID
        default_value: 默认返回值
        
    Returns:
        Movement: 运动对象
    """
```

#### get_movements_by_lane(lane) -> list[Movement]

```python
def get_movements_by_lane(self, lane: Union[Lane, str]) -> list[Movement]:
    """
    获取通过指定车道的所有运动。
    
    Args:
        lane: 车道或车道ID
        
    Returns:
        list[Movement]: 运动列表
    """
```

#### get_movements_by_edge(edge) -> list[Movement]

```python
def get_movements_by_edge(self, edge: Union[Edge, str]) -> list[Movement]:
    """
    获取通过指定路段的所有运动。
    
    Args:
        edge: 路段或路段ID
        
    Returns:
        list[Movement]: 运动列表
    """
```

#### get_movements_by_traffic_light(traffic_light) -> list[Movement]

```python
def get_movements_by_traffic_light(self, traffic_light: Union[TrafficLight, str]) -> list[Movement]:
    """
    获取由指定交通灯控制的所有运动。
    
    Args:
        traffic_light: 交通灯或交通灯ID
        
    Returns:
        list[Movement]: 运动列表
    """
```

#### get_allowed_movements_by_phase(phase) -> list[Movement]

```python
def get_allowed_movements_by_phase(self, phase: Union[TrafficLightPhase, str]) -> list[Movement]:
    """
    获取在指定相位下允许的所有运动。
    
    Args:
        phase: 相位或相位ID
        
    Returns:
        list[Movement]: 运动列表
    """
```

#### get_downstream_movements(movement) -> list[Movement]

```python
def get_downstream_movements(self, movement: Movement) -> list[Movement]:
    """
    获取指定运动的下游运动（即通过目标路段的运动）。
    
    Args:
        movement: 运动对象
        
    Returns:
        list[Movement]: 下游运动列表
    """
```

#### get_upstream_movements(movement) -> list[Movement]

```python
def get_upstream_movements(self, movement: Movement) -> list[Movement]:
    """
    获取指定运动的上游运动（即进入起始路段的运动）。
    
    Args:
        movement: 运动对象
        
    Returns:
        list[Movement]: 上游运动列表
    """
```

#### get_conflict_movements(movement) -> list[Movement]

```python
def get_conflict_movements(self, movement: Movement) -> list[Movement]:
    """
    获取与指定运动冲突的所有运动。
    
    冲突运动定义为：在任何相位下都不能同时放行的运动。
    
    Args:
        movement: 运动对象
        
    Returns:
        list[Movement]: 冲突运动列表
    """
```

---

## 使用示例

### 创建运动网络

```python
from silicontraffic import SiliconSumoEngine
from silicontraffic.movement_modeling import MovementRoadNet

# 初始化引擎
engine = SiliconSumoEngine("config.sumocfg")
engine.reset()

# 创建运动网络
movement_net = MovementRoadNet(engine.road_net)

print(f"运动数量: {len(movement_net.movements)}")
```

### 遍历运动

```python
# 遍历所有运动
for movement in movement_net.movements:
    print(f"运动 {movement.id}:")
    print(f"  起始路段: {movement.from_edge.id}")
    print(f"  目标路段: {movement.to_edge.id}")
    print(f"  车道数: {len(movement.from_lanes)}")
    print(f"  受控于: {movement.traffic_light.id if movement.traffic_light else '无'}")
```

### 查询运动

```python
# 通过路段ID获取运动
movement = movement_net.get_movement("edge1", "edge2")

# 通过路段对象获取运动
edge1 = engine.road_net.get_edge("edge1")
edge2 = engine.road_net.get_edge("edge2")
movement = movement_net.get_movement(edge1, edge2)

# 获取通过指定车道的运动
lane = engine.road_net.get_lane("edge1_0")
movements = movement_net.get_movements_by_lane(lane)

# 获取由指定交通灯控制的运动
tl = engine.road_net.get_traffic_light("tl_0")
controlled_movements = movement_net.get_movements_by_traffic_light(tl)
```

### 分析运动关系

```python
# 获取运动的上下游关系
movement = movement_net.get_movement("edge1", "edge2")

# 获取下游运动
downstream = movement_net.get_downstream_movements(movement)
print(f"下游运动: {[m.id for m in downstream]}")

# 获取上游运动
upstream = movement_net.get_upstream_movements(movement)
print(f"上游运动: {[m.id for m in upstream]}")

# 获取冲突运动
conflicts = movement_net.get_conflict_movements(movement)
print(f"冲突运动: {[m.id for m in conflicts]}")
```

### 相位分析

```python
# 获取相位允许的运动
tl = engine.road_net.get_traffic_light("tl_0")
for phase in tl.phases:
    allowed_movements = movement_net.get_allowed_movements_by_phase(phase)
    print(f"相位 {phase.index} 允许的运动:")
    for m in allowed_movements:
        print(f"  - {m.id}")
```

### 完整示例：基于运动的信号控制

```python
from silicontraffic import SiliconSumoEngine
from silicontraffic.movement_modeling import MovementRoadNet
from silicontraffic.monitor import MovementsMonitor
import random

# 初始化引擎
engine = SiliconSumoEngine("config.sumocfg", use_gui=False)

# 创建运动网络和监控器
movement_net = MovementRoadNet(engine.road_net)
monitor = MovementsMonitor()
monitor.attach_to(engine)

# 获取所有交通灯及其控制的运动
traffic_light_movements = {}
for tl in engine.road_net.traffic_lights:
    movements = movement_net.get_movements_by_traffic_light(tl)
    traffic_light_movements[tl.id] = movements
    print(f"交通灯 {tl.id} 控制 {len(movements)} 个运动")

# 简单的基于压力的信号控制
def pressure_based_control():
    actions = {}
    for tl in engine.road_net.traffic_lights:
        # 获取所有允许当前运动的相位
        best_phase = 0
        max_pressure = -float('inf')
        
        for phase in tl.phases:
            # 计算此相位下所有运动的总压力
            total_pressure = 0
            for movement in movement_net.get_allowed_movements_by_phase(phase):
                pressure = monitor.get_movement_efficient_pressure(movement)
                total_pressure += pressure
            
            if total_pressure > max_pressure:
                max_pressure = total_pressure
                best_phase = phase.index
        
        actions[tl.id] = best_phase
    
    return actions

# 运行仿真
engine.reset()
for _ in range(3600):
    actions = pressure_based_control()
    for tl_id, phase in actions.items():
        engine.set_traffic_light_phase(tl_id, phase)
    engine.step()

engine.terminate()
```
