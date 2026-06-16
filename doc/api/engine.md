# 引擎 API

## 概述

引擎模块提供了交通仿真的核心接口，包括 `TrafficEngine` 抽象基类、`SiliconSumoEngine` 和 `SiliconCityFlowEngine` 实现类。

## TrafficEngine（抽象基类）

### 类定义

```python
class TrafficEngine(ABC):
    """
    交通环境引擎的抽象基类。
    
    提供：
        - `road_net` 属性，用于访问道路网络结构信息
        - `get_time` 方法，获取当前仿真时间
        - `get_lane_vehicle_ids` 方法，获取车道上的车辆ID
        - `get_vehicle_info` 方法，获取车辆信息
        - `get_traffic_light_phase` 方法，获取交通灯相位
        - `set_traffic_light_phase` 方法，设置交通灯相位
    """
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `road_net` | RoadNet | 道路网络对象 |
| `step_handlers` | List[Callable] | 步骤处理器列表 |

### 方法

#### reset()

重置交通环境到初始状态。

```python
def reset(self):
    """
    Reset the traffic environment to its initial state.
    """
```

#### terminate()

终止交通仿真。

```python
def terminate(self):
    """
    Terminate the traffic environment simulation.
    """
```

#### step(step_num=1)

执行仿真步骤。

```python
def step(self, step_num: int = 1):
    """
    Perform multiple simulation steps.
    
    Args:
        step_num (int): 仿真步数，默认为1
    """
```

#### on_step(handler)

注册步骤处理器。

```python
def on_step(self, handler: Callable[['TrafficEngine'], None]):
    """
    Register a step handler function.
    
    Args:
        handler: 步骤处理器函数
        
    Examples:
        @my_env.on_step
        def my_handler(engine):
            # do something
            pass
    """
```

#### get_time() -> float

获取当前仿真时间。

```python
def get_time(self) -> float:
    """
    Get the current simulation time.
    
    Returns:
        float: 当前仿真时间
    """
```

#### get_vehicle_ids() -> list[str]

获取所有运行中车辆的ID。

```python
def get_vehicle_ids(self) -> list[str]:
    """
    Get the IDs of all running vehicles.
    
    Returns:
        list[str]: 所有车辆ID列表
    """
```

#### get_lane_vehicle_ids(lane) -> list[str]

获取指定车道上的车辆ID。

```python
def get_lane_vehicle_ids(self, lane: Union[str, Lane]) -> list[str]:
    """
    Get the IDs of vehicles on a lane.
    
    Args:
        lane: 车道ID或Lane对象
        
    Returns:
        list[str]: 车道上的车辆ID列表
    """
```

#### get_vehicle_info(vehicle_id) -> Vehicle

获取指定车辆的信息。

```python
def get_vehicle_info(self, vehicle_id) -> Vehicle:
    """
    Get the information of a vehicle.
    
    Args:
        vehicle_id: 车辆ID
        
    Returns:
        Vehicle: 车辆信息对象
    """
```

#### get_traffic_light_phase(traffic_light) -> TrafficLightPhase

获取指定交通灯的当前相位。

```python
def get_traffic_light_phase(self, traffic_light: Union[str, TrafficLight]) -> TrafficLightPhase:
    """
    Get the phase of a traffic light.
    
    Args:
        traffic_light: 交通灯ID或TrafficLight对象
        
    Returns:
        TrafficLightPhase: 交通灯相位对象
    """
```

#### set_traffic_light_phase(traffic_light, phase)

设置指定交通灯的相位。

```python
def set_traffic_light_phase(self, traffic_light: Union[str, TrafficLight], phase: Union[int, TrafficLightPhase]):
    """
    Set the phase of a traffic light.
    
    Args:
        traffic_light: 交通灯ID或TrafficLight对象
        phase: 相位索引或TrafficLightPhase对象
    """
```

#### get_lane_queue_length(lane, speed_threshold=0.1) -> int

获取车道排队长度。

```python
def get_lane_queue_length(self, lane: Union[str, Lane], speed_threshold: float = 0.1) -> int:
    """
    Get the queue length of a lane.
    
    Args:
        lane: 车道ID或Lane对象
        speed_threshold: 速度阈值，低于此值视为排队车辆
        
    Returns:
        int: 排队车辆数量
    """
```

#### get_last_step_departed_vehicle_ids() -> list[str]

获取上一步出发的车辆ID。

```python
def get_last_step_departed_vehicle_ids(self) -> list[str]:
    """
    Get the IDs of vehicles that departed in the last step.
    
    Returns:
        list[str]: 上一步出发的车辆ID列表
    """
```

#### get_last_step_arrived_vehicle_ids() -> list[str]

获取上一步到达的车辆ID。

```python
def get_last_step_arrived_vehicle_ids(self) -> list[str]:
    """
    Get the IDs of vehicles that arrived in the last step.
    
    Returns:
        list[str]: 上一步到达的车辆ID列表
    """
```

---

## SiliconSumoEngine

### 类定义

```python
class SiliconSumoEngine(TrafficEngine):
    """
    SUMO 仿真引擎实现。
    """
```

### 构造函数

```python
def __init__(self, sumocfg_path: str, log_path: str = "temp/", port: int = None, 
             seed: int = None, time_to_teleport: int = 600, 
             waiting_time_memory: int = 100, use_gui: bool = False):
    """
    Args:
        sumocfg_path: SUMO 配置文件路径
        log_path: 日志输出路径，默认为 "temp/"
        port: TraCI 连接端口，自动分配为 None
        seed: 随机种子，随机为 None
        time_to_teleport: 车辆 teleport 时间，默认为 600
        waiting_time_memory: 等待时间记忆，默认为 100
        use_gui: 是否启用图形界面，默认为 False
    """
```

### 属性扩展

| 属性 | 类型 | 说明 |
|------|------|------|
| `sumocfg_path` | str | SUMO 配置文件路径 |
| `port` | int | TraCI 端口 |
| `seed` | int | 随机种子 |
| `use_gui` | bool | 是否启用GUI |
| `traffic_light_ids` | list[str] | 交通灯ID列表 |

### 扩展方法

#### update_road_net()

更新道路网络信息。

```python
def update_road_net(self):
    """
    Parse sumocfg to get net-file path and load road net.
    """
```

### TraCI 域接口

SiliconSumoEngine 暴露了完整的 TraCI 域接口，可直接使用：

```python
# 访问 TraCI 域
engine.busstop      # 公交站域
engine.calibrator   # 校准器域
engine.edge         # 路段域
engine.gui          # 图形界面域
engine.inductionloop # 感应线圈域
engine.junction     # 路口域
engine.lane         # 车道域
engine.meandata     # 均值数据域
engine.person       # 人员域
engine.route        # 路线域
engine.simulation   # 仿真域
engine.trafficlight # 交通灯域
engine.vehicle      # 车辆域
engine.vehicletype  # 车辆类型域
```

---

## SiliconCityFlowEngine

### 类定义

```python
class SiliconCityFlowEngine(TrafficEngine):
    """
    CityFlow 仿真引擎实现。
    """
```

### 构造函数

```python
def __init__(self, path_to_cityflow_config: str, thread_num: int = 8):
    """
    Args:
        path_to_cityflow_config: CityFlow 配置文件路径
        thread_num: 线程数，默认为 8
    """
```

### 属性扩展

| 属性 | 类型 | 说明 |
|------|------|------|
| `path_to_cityflow_config` | str | CityFlow 配置文件路径 |
| `thread_num` | int | 线程数 |
| `traffic_light_ids` | list[str] | 交通灯ID列表 |

---

## 使用示例

### 基础仿真循环

```python
from silicontraffic import SiliconSumoEngine

# 初始化引擎
engine = SiliconSumoEngine("config.sumocfg", use_gui=True)

# 重置仿真
engine.reset()

# 运行仿真
for _ in range(1000):
    engine.step()
    
    # 获取当前时间
    current_time = engine.get_time()
    
    # 获取车辆信息
    vehicles = engine.get_vehicle_ids()
    for vid in vehicles[:5]:  # 只查看前5辆车
        vehicle = engine.get_vehicle_info(vid)
        print(f"车辆 {vid}: 速度={vehicle.speed:.2f}m/s, 位置={vehicle.lane_position:.2f}m")
    
    # 设置交通灯
    engine.set_traffic_light_phase("tl_0", 0)

# 终止仿真
engine.terminate()
```

### 注册步骤处理器

```python
from silicontraffic import SiliconCityFlowEngine

engine = SiliconCityFlowEngine("cityflow.config")

# 注册步骤处理器
@engine.on_step
def log_step(engine):
    """每步输出日志"""
    time = engine.get_time()
    num_vehicles = len(engine.get_vehicle_ids())
    print(f"时间: {time}, 车辆数: {num_vehicles}")

engine.reset()
engine.step(100)
engine.terminate()
```
