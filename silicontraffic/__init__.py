"""
## Silicon Traffic

This module provides a generic interface for SUMO and CityFlow.
"""
import warnings

try:
    from .ssumo import SiliconSumoEngine, load_sumo_road_net
except (ImportError, ModuleNotFoundError):
    warnings.warn("SUMO module not found. Related features will not work available.")

try:
    from .scityflow import SiliconCityFlowEngine, load_cityflow_road_net
except (ImportError, ModuleNotFoundError):
    warnings.warn("CityFlow module not found. Related features will not work available.")
