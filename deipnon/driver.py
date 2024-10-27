import os
import json
import zipfile
import platform
from pathlib import Path
from enum import Enum

import requests

from .utils import get_logger, download_file

logger = get_logger(__name__)


class WEB_DRIVER_TYPE(Enum):
    CHROME = "chrome"
    EDGE = "edge"
    FIREFOX = "firefox"


def check_webdriver(webdriver_path: str):
    """check whether webdriver exists"""
    return os.path.exists(webdriver_path)


def download_webdriver(web_driver_type: WEB_DRIVER_TYPE, webdriver_path: str):
    webdriver_folder = os.path.dirname(os.path.normpath(webdriver_path))
    logger.info("Auto downloading webdriver to %s", webdriver_folder)
    if len(webdriver_folder) > 0 and not os.path.exists(
        webdriver_folder
    ):  # webdriver_folder may be "" for cwd
        os.makedirs(webdriver_folder)

    system = platform.system()
    if system != "Windows":
        raise RuntimeError(f"{system} not supported!")

    if web_driver_type == WEB_DRIVER_TYPE.CHROME:
        CHROME_WEBDRIVER_LIST_URL = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        try:
            resp = requests.get(CHROME_WEBDRIVER_LIST_URL, timeout=10)
            enable_verify = True
        except requests.exceptions.SSLError:
            resp = requests.get(
                CHROME_WEBDRIVER_LIST_URL, timeout=10, verify=False
            )
            enable_verify = False
        webdriver_list = json.loads(resp.text)

        target_version = webdriver_list["versions"][0]
        logger.info("Webdriver version: %s", target_version["version"])

        download_url = None
        for item in target_version["downloads"]["chrome"]:
            if item["platform"] == "win64":
                download_url = item["url"]
                break

        webdriver_file_name = os.path.join(webdriver_folder, "webdriver.zip")
        download_file(download_url, webdriver_file_name, enable_verify)

        with zipfile.ZipFile(webdriver_file_name, "r") as zip_ref:
            zip_ref.extractall(webdriver_folder)

        for path in Path(webdriver_folder).rglob("chrome.exe"):
            return path.as_posix()
    elif web_driver_type == WEB_DRIVER_TYPE.EDGE:
        logger.error("Please downalod and install webdriver manually")
        raise NotImplementedError

    elif web_driver_type == WEB_DRIVER_TYPE.FIREFOX:
        FIREFOX_WEBDRIVER_LIST_URL = (
            "https://api.github.com/repos/mozilla/geckodriver/releases/latest"
        )
        try:
            resp = requests.get(FIREFOX_WEBDRIVER_LIST_URL, timeout=10)
            enable_verify = True
        except requests.exceptions.SSLError:
            resp = requests.get(
                FIREFOX_WEBDRIVER_LIST_URL, timeout=10, verify=False
            )
            enable_verify = False
        webdriver_list = json.loads(resp.text)

        logger.info("Webdriver version: %s", webdriver_list["tag_name"])

        download_url = None
        for item in webdriver_list["assets"]:
            if "win64" in item["name"]:
                download_url = item["browser_download_url"]
                break

        webdriver_file_name = os.path.join(webdriver_folder, "webdriver.zip")
        download_file(download_url, webdriver_file_name, enable_verify)

        with zipfile.ZipFile(webdriver_file_name, "r") as zip_ref:
            zip_ref.extractall(webdriver_folder)

        for path in Path(webdriver_folder).rglob("geckodriver.exe"):
            return path.as_posix()

    raise RuntimeError("Download file error")
