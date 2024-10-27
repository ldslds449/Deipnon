import os
import sys
import logging

import requests


def get_logger(name: str):
    """get a logger from the name"""
    level = os.environ.get("LOG_LEVEL", "INFO")
    new_logger = logging.getLogger(name)
    new_logger.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler_formatter = logging.Formatter(
        "[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
    stream_handler.setFormatter(stream_handler_formatter)

    new_logger.addHandler(stream_handler)
    return new_logger


logger = get_logger(__name__)


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


def download_file(
    url: str, file_path: str, verify: bool = True, timeout: int = 30
):
    with requests.get(url, stream=True, verify=verify, timeout=timeout) as r:
        r.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
