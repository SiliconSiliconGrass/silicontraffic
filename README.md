# Silicon Traffic Env

A unified traffic simulation environment interface for SUMO and CityFlow, providing a consistent API for working with different traffic simulation backends.

## Features

- Unified interface for SUMO and CityFlow traffic simulators
- Road network abstraction
- Vehicle and traffic light management
- Movement modeling for traffic analysis
- Monitoring capabilities for traffic statistics

## Installation

### Prerequisites

- Python 3.9 or higher
- For SUMO support: [SUMO](https://sumo.dlr.de/docs/Installing.html) (Simulation of Urban MObility)
- For CityFlow support: [CityFlow](https://github.com/cityflow-project/CityFlow) (A multi-agent reinforcement learning environment for large-scale city traffic scenario)

### Install the package

```bash
# Install from source
pip install .
```

## Usage Examples

### SUMO Example

```python
from silicontraffic.ssumo import Engine

# Initialize SUMO engine
sumo_cfg_path = "examples/data/sumo/MoST/most.sumocfg"
engine = Engine(sumo_cfg_path, use_gui=True)

# Reset the simulation
engine.reset()

# Run simulation steps
for _ in range(100):
    engine.step()

# Terminate the simulation
engine.terminate()
```

### CityFlow Example

```python
from silicontraffic.scityflow import Engine

# Initialize CityFlow engine
cityflow_config_path = "examples/data/cityflow/hangzhou/cityflow.config"
engine = Engine(cityflow_config_path)

# Reset the simulation
engine.reset()

# Run simulation steps
for _ in range(100):
    engine.step()
```

## Project Structure

```
silicon-traffic-env/
├── examples/             # Example scripts and data
│   ├── data/             # Test data for SUMO and CityFlow
│   └── scripts/          # Example usage scripts
├── silicontraffic/       # Main package directory
│   ├── monitor/          # Traffic monitoring modules
│   ├── movement_modeling/ # Traffic movement modeling
│   ├── road_net/         # Road network abstraction
│   ├── scityflow/        # CityFlow integration
│   ├── ssumo/            # SUMO integration
│   └── __init__.py       # Package initialization
├── pyproject.toml        # Build configuration
├── setup.cfg             # Package configuration
└── README.md             # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
