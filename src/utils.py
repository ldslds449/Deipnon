import os
import sys
import logging


def get_logger(name: str):
    """get a logger from the name"""
    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
    return logger


logger = get_logger(__file__)


def get_config_file_path():
    """find out config file path from arguments and environment variables or using default values"""
    if len(sys.argv) > 1:
        config_path = sys.argv[-1]
        logger.info("config file path from arguement: %s", config_path)
        return config_path
    config_path = os.environ.get("CONFIG_PATH", None)
    if config_path is not None:
        logger.info(
            "config file path from environment variable: %s", config_path
        )
        return config_path
    else:
        DEFAULT_CONFIG_PATH = "config.toml"
        logger.info(
            "config file path from default value: %s", DEFAULT_CONFIG_PATH
        )
        return DEFAULT_CONFIG_PATH
