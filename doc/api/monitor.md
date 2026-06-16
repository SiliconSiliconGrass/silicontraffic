# 监控器 API

## 概述

监控器模块提供了交通数据的收集和统计功能，包括全局监控和运动级监控。

## Monitor（抽象基类）

```python
class Monitor(ABC):
    """
    交通监控器的抽象基类。
    """
    
    def __init__(self):
        self._auto_reset = False
    
    @abstractmethod
    def attach_to(self, engine: TrafficEngine):
        pass
    
    @abstractmethod
    def reset(self):
        """重置监控器"""
```

### 方法

#### attach_to(engine)

将监控器附加到引擎。

```python
def attach_to(self, engine: TrafficEngine):
    """
    Attach the monitor to a traffic engine.
    
    Args:
        engine: TrafficEngine 对象
    """
```

#### reset()

重置监控器数据。

```python
def reset(self):
    """
    Reset the monitor.
    """
```

#### setup_auto_reset(engine)

设置自动重置功能。

```python
def setup_auto_reset(self, engine: TrafficEngine):
    """
    Setup auto reset function, so that the monitor will reset automatically 
    when engine is reset.
    """
```

---

## GlobalMonitor（全局监控器）

### 类定义

```python
class GlobalMonitor(Monitor):
    """
    全局统计监控器。
    
    提供：
        - get_avg_waiting_time: 平均等待时间
        - get_avg_travel_time: 平均旅行时间
        - get_avg_stop_count: 平均停车次数
        - get_avg_queue_length: 平均排队长度
        - get_throughput: 吞吐量
    """
```

### 使用方法

```python
from silicontraffic import SiliconSumoEngine
from silicontraffic.monitor import GlobalMonitor

# 初始化引擎
engine = SiliconSumoEngine("config.sumocfg")

# 创建监控器并附加
monitor = GlobalMonitor()
monitor.attach_to(engine)

# 运行仿真
engine.reset()
for _ in range(1000):
    engine.step()

# 获取统计数据
avg_waiting = monitor.get_avg_waiting_time()
avg_travel = monitor.get_avg_travel_time()
avg_stops = monitor.get_avg_stop_times()
avg_queue = monitor.get_avg_queue_length()
throughput = monitor.get_throughput()

engine.terminate()
```

### 方法详解

#### get_avg_waiting_time() -> float

```python
def get_avg_waiting_time(self) -> float:
    """
    返回所有记录车辆的平均等待时间。
    
    Returns:
        float: 平均等待时间（秒）
    """
```

#### get_avg_stop_times() -> float

```python
def get_avg_stop_times(self) -> float:
    """
    返回所有记录车辆的平均停车次数。
    
    Returns:
        float: 平均停车次数
    """
```

#### get_avg_travel_time() -> float

```python
def get_avg_travel_time(self) -> float:
    """
    返回所有到达车辆的平均旅行时间。
    
    Returns:
        float: 平均旅行时间（秒）
    """
```

#### get_avg_queue_length() -> float

```python
def get_avg_queue_length(self) -> float:
    """
    返回所有车道的平均排队长度。
    
    Returns:
        float: 平均排队长度（车辆数）
    """
```

#### get_throughput() -> int

```python
def get_throughput(self) -> int:
    """
    返回到达的车辆总数（吞吐量）。
    
    Returns:
        int: 到达车辆数
    """
```

---

## MovementsMonitor（运动监控器）

### 类定义

```python
class MovementsMonitor(Monitor):
    """
    运动级数据监控器。
    
    提供运动级别的统计数据，如排队长度、有效车辆数、压力等。
    """
```

### 使用方法

```python
from silicontraffic import SiliconSumoEngine
from silicontraffic.monitor import MovementsMonitor
from silicontraffic.movement_modeling import MovementRoadNet

# 初始化引擎
engine = SiliconSumoEngine("config.sumocfg")

# 创建监控器并附加
monitor = MovementsMonitor()
monitor.attach_to(engine)

# 获取运动网络
movement_net = monitor.road_net

# 运行仿真
engine.reset()
for _ in range(1000):
    engine.step()

# 获取特定运动的统计数据
movement = movement_net.get_movement("edge1", "edge2")
queue_length = monitor.get_movement_sum_queue_length(movement)
effective_vehicles = monitor.get_movement_effective_vehicles(movement)
pressure = monitor.get_movement_efficient_pressure(movement)

engine.terminate()
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `road_net` | MovementRoadNet | 运动网络对象 |

### 方法详解

#### get_movement_sum_queue_length(movement) -> int

```python
def get_movement_sum_queue_length(self, movement: Union[Movement, str]) -> int:
    """
    获取运动的总排队长度。
    
    Args:
        movement: Movement 对象或运动ID
        
    Returns:
        int: 排队车辆总数
    """
```

#### get_movement_avg_queue_length(movement) -> float

```python
def get_movement_avg_queue_length(self, movement: Union[Movement, str]) -> float:
    """
    获取运动的平均排队长度。
    
    Args:
        movement: Movement 对象或运动ID
        
    Returns:
        float: 平均排队长度
    """
```

#### get_movement_max_lane_length(movement) -> float

```python
def get_movement_max_lane_length(self, movement: Union[Movement, str]) -> float:
    """
    获取运动的最大车道长度。
    
    Args:
        movement: Movement 对象或运动ID
        
    Returns:
        float: 最大车道长度（米）
    """
```

#### get_movement_effective_vehicles(movement, effective_range=100) -> int

```python
def get_movement_effective_vehicles(self, movement: Union[Movement, str], effective_range: float = 100) -> int:
    """
    获取运动的有效车辆数（在有效范围内的车辆）。
    
    Args:
        movement: Movement 对象或运动ID
        effective_range: 有效范围（米），默认为100
        
    Returns:
        int: 有效车辆数
    """
```

#### get_movement_efficient_pressure(movement) -> float

```python
def get_movement_efficient_pressure(self, movement: Union[Movement, str]) -> float:
    """
    计算运动的有效压力（上游排队长度 - 下游排队长度）。
    
    Args:
        movement: Movement 对象或运动ID
        
    Returns:
        float: 有效压力值
    """
```

---

## 使用示例

### 综合监控示例

```python
from silicontraffic import SiliconSumoEngine
from silicontraffic.monitor import GlobalMonitor, MovementsMonitor
from tqdm import tqdm

# 初始化引擎
engine = SiliconSumoEngine("examples/data/sumo/MoST/most.sumocfg", use_gui=False)

# 创建监控器
global_monitor = GlobalMonitor()
movements_monitor = MovementsMonitor()

# 附加到引擎
global_monitor.attach_to(engine)
movements_monitor.attach_to(engine)

# 获取运动网络
movement_net = movements_monitor.road_net

# 运行仿真
num_steps = 3600
engine.reset()

for step in tqdm(range(num_steps)):
    engine.step()
    
    # 每100步输出一次统计
    if step % 100 == 0:
        print(f"\n=== 时间步 {step} ===")
        print(f"平均排队长度: {global_monitor.get_avg_queue_length():.2f}")
        print(f"平均等待时间: {global_monitor.get_avg_waiting_time():.2f}s")
        print(f"平均旅行时间: {global_monitor.get_avg_travel_time():.2f}s")
        print(f"吞吐量: {global_monitor.get_throughput()}")
        
        # 输出第一个运动的压力
        if movement_net.movements:
            first_movement = movement_net.movements[0]
            pressure = movements_monitor.get_movement_efficient_pressure(first_movement)
            print(f"运动 {first_movement.id} 压力: {pressure:.2f}")

engine.terminate()

# 输出最终统计
print("\n=== 最终统计 ===")
print(f"平均排队长度: {global_monitor.get_avg_queue_length():.2f}")
print(f"平均等待时间: {global_monitor.get_avg_waiting_time():.2f}s")
print(f"平均停车次数: {global_monitor.get_avg_stop_times():.2f}")
print(f"平均旅行时间: {global_monitor.get_avg_travel_time():.2f}s")
print(f"总吞吐量: {global_monitor.get_throughput()}")
```

### 多引擎监控示例

```python
from silicontraffic import SiliconSumoEngine, SiliconCityFlowEngine
from silicontraffic.monitor import GlobalMonitor

# 创建两个引擎的监控器
sumo_monitor = GlobalMonitor()
cityflow_monitor = GlobalMonitor()

# SUMO 仿真
sumo_engine = SiliconSumoEngine("sumo_config.sumocfg")
sumo_monitor.attach_to(sumo_engine)
sumo_engine.reset()
sumo_engine.step(1000)
sumo_engine.terminate()

# CityFlow 仿真
cityflow_engine = SiliconCityFlowEngine("cityflow_config.json")
cityflow_monitor.attach_to(cityflow_engine)
cityflow_engine.reset()
cityflow_engine.step(1000)
cityflow_engine.terminate()

# 比较结果
print("=== SUMO 结果 ===")
print(f"平均排队长度: {sumo_monitor.get_avg_queue_length()}")
print(f"平均等待时间: {sumo_monitor.get_avg_waiting_time()}")

print("\n=== CityFlow 结果 ===")
print(f"平均排队长度: {cityflow_monitor.get_avg_queue_length()}")
print(f"平均等待时间: {cityflow_monitor.get_avg_waiting_time()}")
```
