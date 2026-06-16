# Silicon Traffic Env 文档

Silicon Traffic Env 是一个统一的交通仿真环境接口，为 SUMO 和 CityFlow 提供一致的 API。

## 项目简介

Silicon Traffic Env 旨在为交通仿真研究提供一个统一的抽象层，使得开发者可以使用相同的 API 来操作不同的交通仿真后端（SUMO 和 CityFlow）。

### 核心特性

- **统一接口**: 为 SUMO 和 CityFlow 提供一致的 API，降低学习成本
- **道路网络抽象**: 提供统一的道路网络数据模型，包括路口、路段、车道、交通灯等
- **车辆管理**: 提供车辆信息查询和管理功能
- **交通灯控制**: 支持交通灯相位查询和设置
- **监控系统**: 提供全局和运动级别的监控功能
- **运动建模**: 支持基于路段的运动分析

### 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户应用层                                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌───────────────┐  ┌───────────────────┐     │
│  │  Monitor    │  │  MovementRoad │  │  自定义算法       │     │
│  │  (监控器)    │  │  Net (运动网络) │  │  (如RL策略)      │     │
│  └──────┬──────┘  └───────┬───────┘  └─────────┬─────────┘     │
│         │                 │                    │                │
├─────────┼─────────────────┼────────────────────┼────────────────┤
│         │                 │                    │                │
│  ┌──────▼─────────────────▼────────────────────▼────────┐      │
│  │                  TrafficEngine (抽象引擎接口)         │      │
│  └──────────────────────────────────────────────────────┘      │
│         │                            │                         │
│  ┌──────▼──────┐              ┌──────▼──────┐                 │
│  │ SiliconSumo │              │ SiliconCity │                 │
│  │   Engine    │              │   FlowEngine│                 │
│  └─────────────┘              └─────────────┘                 │
├─────────────────────────────────────────────────────────────────┤
│                    仿真后端层                                   │
│        ┌───────────────┐              ┌───────────────┐       │
│        │     SUMO      │              │   CityFlow    │       │
│        └───────────────┘              └───────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 安装依赖

```bash
# 安装包
pip install .

# 安装 SUMO 支持
pip install .[sumo]

# 安装 CityFlow（需单独安装）
pip install cityflow
```

### 基本使用

```python
from silicontraffic import SiliconSumoEngine

# 初始化引擎
engine = SiliconSumoEngine("path/to/config.sumocfg", use_gui=True)

# 重置仿真
engine.reset()

# 运行仿真
for _ in range(100):
    engine.step()

# 终止仿真
engine.terminate()
```

## 目录结构

```
silicon-traffic-env/
├── doc/                    # 文档目录
│   ├── index.md            # 主文档入口
│   ├── quickstart.md       # 快速入门
│   └── api/                # API 文档
│       ├── engine.md       # 引擎 API
│       ├── road_net.md     # 道路网络 API
│       ├── monitor.md      # 监控器 API
│       └── movement.md     # 运动建模 API
├── examples/               # 示例代码
├── silicontraffic/         # 主包目录
└── ...
```

## 模块说明

| 模块 | 说明 |
|------|------|
| `silicontraffic` | 主包，提供统一接口 |
| `silicontraffic.ssumo` | SUMO 仿真引擎实现 |
| `silicontraffic.scityflow` | CityFlow 仿真引擎实现 |
| `silicontraffic.road_net` | 道路网络抽象模型 |
| `silicontraffic.monitor` | 交通监控模块 |
| `silicontraffic.movement_modeling` | 运动建模模块 |

## 文档导航

- [快速入门](quickstart.md)
- [引擎 API](api/engine.md)
- [道路网络 API](api/road_net.md)
- [监控器 API](api/monitor.md)
- [运动建模 API](api/movement.md)
