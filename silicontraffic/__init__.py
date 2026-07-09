"""
## Silicon Traffic

This module provides a generic interface for SUMO and CityFlow.
"""

import logging
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

try:
    from .ssumo import SiliconSumoEngine, load_sumo_road_net
    logger.info("SUMO module found.")
except (ImportError, ModuleNotFoundError):
    logger.warning("SUMO module not found. Related features will not work available.")

try:
    from .scityflow import SiliconCityFlowEngine, load_cityflow_road_net
    logger.info("CityFlow module found.")
except (ImportError, ModuleNotFoundError):
    logger.warning("CityFlow module not found. Related features will not work available.")
