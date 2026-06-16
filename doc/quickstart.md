# 快速入门

## 安装指南

### 环境要求

- Python 3.9 或更高版本
- SUMO（可选，用于 SUMO 仿真支持）
- CityFlow（可选，用于 CityFlow 仿真支持）

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/SiliconSiliconGrass/silicontraffic.git
cd silicon-traffic-env

# 安装核心包
pip install .

# 安装 SUMO 支持
pip install .[sumo]

# 安装 CityFlow
pip install cityflow
```

### 安装验证

```python
from silicontraffic import SiliconSumoEngine, SiliconCityFlowEngine
print("Silicon Traffic Env 安装成功！")
```

## SUMO 引擎入门

### 基本使用

```python
from silicontraffic import SiliconSumoEngine

# 初始化 SUMO 引擎
sumo_cfg_path = "examples/data/sumo/MoST/most.sumocfg"
engine = SiliconSumoEngine(sumo_cfg_path, use_gui=True)

# 重置仿真
engine.reset()

# 运行仿真步骤
for _ in range(100):
    engine.step()

# 终止仿真
engine.terminate()
```

### 关键参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `sumocfg_path` | str | 必填 | SUMO 配置文件路径 |
| `log_path` | str | "temp/" | 日志输出路径 |
| `port` | int | 自动分配 | TraCI 连接端口 |
| `seed` | int | 随机 | 随机种子 |
| `time_to_teleport` | int | 600 | 车辆 teleport 时间 |
| `use_gui` | bool | False | 是否启用图形界面 |

## CityFlow 引擎入门

### 基本使用

```python
from silicontraffic import SiliconCityFlowEngine

# 初始化 CityFlow 引擎
cityflow_config_path = "examples/data/cityflow/hangzhou/cityflow.config"
engine = SiliconCityFlowEngine(cityflow_config_path)

# 重置仿真
engine.reset()

# 运行仿真步骤
for _ in range(100):
    engine.step()

# 终止仿真
engine.terminate()
```

### 关键参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path_to_cityflow_config` | str | 必填 | CityFlow 配置文件路径 |
| `thread_num` | int | 8 | 线程数 |

## 交通灯控制示例

```python
from silicontraffic import SiliconSumoEngine
import random

# 初始化引擎
engine = SiliconSumoEngine("path/to/config.sumocfg")
engine.reset()

# 获取所有交通灯
traffic_lights = engine.road_net.traffic_lights

# 随机设置交通灯相位
for _ in range(100):
    for tl in traffic_lights:
        phase = random.randint(0, len(tl.phases) - 1)
        engine.set_traffic_light_phase(tl.id, phase)
    engine.step()

engine.terminate()
```

## 监控器使用示例

```python
from silicontraffic import SiliconSumoEngine
from silicontraffic.monitor import GlobalMonitor

# 初始化引擎和监控器
engine = SiliconSumoEngine("path/to/config.sumocfg")
monitor = GlobalMonitor()
monitor.attach_to(engine)

# 运行仿真
engine.reset()
for _ in range(1000):
    engine.step()

# 获取统计数据
print(f"平均排队长度: {monitor.get_avg_queue_length()}")
print(f"平均等待时间: {monitor.get_avg_waiting_time()}")
print(f"平均旅行时间: {monitor.get_avg_travel_time()}")

engine.terminate()
```

## 运动建模示例

```python
from silicontraffic import SiliconSumoEngine
from silicontraffic.movement_modeling import MovementRoadNet

# 初始化引擎
engine = SiliconSumoEngine("path/to/config.sumocfg")
engine.reset()

# 创建运动网络
movement_net = MovementRoadNet(engine.road_net)

# 获取所有运动
movements = movement_net.movements

# 获取特定运动的排队长度
movement = movement_net.get_movement("edge1", "edge2")
queue_length = engine.get_lane_queue_length(movement.from_lanes[0])

engine.terminate()
```

## 常用操作汇总

### 获取车辆信息

```python
# 获取所有车辆ID
vehicle_ids = engine.get_vehicle_ids()

# 获取特定车辆信息
vehicle = engine.get_vehicle_info("vehicle_0")
print(f"车辆速度: {vehicle.speed}")
print(f"车辆位置: {vehicle.lane_position}")
print(f"车辆路线: {vehicle.route}")
```

### 获取车道信息

```python
# 获取车道上的车辆
lane_vehicles = engine.get_lane_vehicle_ids("lane_0")

# 获取车道排队长度
queue_length = engine.get_lane_queue_length("lane_0")
```

### 获取交通灯信息

```python
# 获取交通灯当前相位
phase = engine.get_traffic_light_phase("tl_0")

# 设置交通灯相位
engine.set_traffic_light_phase("tl_0", 0)
```

## 完整示例

以下是一个完整的交通信号控制仿真示例：

```python
from silicontraffic import SiliconSumoEngine
from silicontraffic.monitor import GlobalMonitor, MovementsMonitor
import random
from tqdm import tqdm

# 初始化引擎
engine = SiliconSumoEngine("examples/data/sumo/MoST/most.sumocfg", use_gui=False)

# 创建监控器
global_monitor = GlobalMonitor()
movements_monitor = MovementsMonitor()
global_monitor.attach_to(engine)
movements_monitor.attach_to(engine)

# 随机选择相位
def choose_phases():
    return {
        tl.id: random.randint(0, len(tl.phases) - 1)
        for tl in engine.road_net.traffic_lights
    }

# 运行仿真
num_steps = 3600
min_phase_duration = 30

engine.reset()
for step in tqdm(range(int(num_steps / min_phase_duration))):
    actions = choose_phases()
    for tl_id, phase in actions.items():
        engine.set_traffic_light_phase(tl_id, phase)
    engine.step(step_num=min_phase_duration)

# 获取统计结果
print(f"平均排队长度: {global_monitor.get_avg_queue_length()}")
print(f"平均等待时间: {global_monitor.get_avg_waiting_time()}")
print(f"平均旅行时间: {global_monitor.get_avg_travel_time()}")
print(f"吞吐量: {global_monitor.get_throughput()}")

engine.terminate()
```
