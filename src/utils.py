import os
import sys
import json
import zipfile
import logging
import requests
import platform
import urllib.request
from pathlib import Path


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


def check_webdriver(webdriver_path: str):
    """check whether webdriver exists"""
    return os.path.exists(webdriver_path)


def download_webdriver(webdriver_path: str):
    webdriver_folder = os.path.dirname(os.path.normpath(webdriver_path))
    logger.info("Auto downloading webdriver to %s", webdriver_folder)
    if not os.path.exists(webdriver_folder):
        os.makedirs(webdriver_folder)

    system = platform.system()
    if system != "Windows":
        raise RuntimeError(f"{system} not supported!")

    CHROME_WEBDRIVER_LIST_URL = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    webdriver_list = json.loads(
        requests.get(CHROME_WEBDRIVER_LIST_URL, timeout=10).text
    )

    target_version = webdriver_list["versions"][0]
    logger.info("Webdriver version: %s", target_version["version"])

    download_url = None
    for item in target_version["downloads"]["chrome"]:
        if item["platform"] == "win64":
            download_url = item["url"]
            break

    webdriver_file_name = os.path.join(webdriver_folder, "webdriver.zip")
    urllib.request.urlretrieve(download_url, webdriver_file_name)

    with zipfile.ZipFile(webdriver_file_name, "r") as zip_ref:
        zip_ref.extractall(webdriver_folder)

    for path in Path(webdriver_folder).rglob("chrome.exe"):
        return path.as_posix()

    raise RuntimeError("Download file error")
