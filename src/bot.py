import contextlib
import logging
import time
import os

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from PIL import Image

from .config import BotConfig
from .predict import Captcha

logger = logging.getLogger(__file__)


class Bot:
    driver: webdriver.Chrome = None
    model: Captcha = None

    def __init__(self, bot_config: BotConfig):
        self.bot_config = bot_config
        self.initial_model()
        self.initial_browser()

    def __del__(self):
        if self.driver:
            self.driver.quit()

    def initial_model(self):
        model_path = self.bot_config.model_path

        assert model_path is not None and os.path.exists(
            model_path
        ), f"model_path ({model_path}) is invalid"

        logger.info("Initial yolo model %s", model_path)
        self.model = Captcha(model_path)

    def initial_browser(self):
        web_driver_path, proxy_server, headless = (
            self.bot_config.web_driver_path,
            self.bot_config.proxy_server,
            self.bot_config.headless,
        )

        assert web_driver_path.endswith(
            ("chrome.exe", "chrome")
        ), f"web driver path ({web_driver_path}) is not valid, it should be a path of chrome executable"

        logger.info("Initial web driver %s", web_driver_path)

        service = webdriver.ChromeService()
        option = webdriver.ChromeOptions()
        option.add_argument("--disable-gpu")
        if headless:
            option.add_argument("--headless=new")
        # https://stackoverflow.com/questions/65080685/usb-usb-device-handle-win-cc1020-failed-to-read-descriptor-from-node-connectio
        option.add_experimental_option("excludeSwitches", ["enable-logging"])

        option.binary_location = web_driver_path
        if proxy_server:
            option.add_argument(f"--proxy-server={proxy_server}")
        self.driver = webdriver.Chrome(service=service, options=option)

    def __get_image(
        self, image_url: str, auth_key: str, auth_token: str, timeout_sec: int
    ) -> Image.Image:
        cookies = {auth_key: auth_token}

        with requests.get(
            image_url, cookies=cookies, stream=True, timeout=timeout_sec
        ) as r:
            img = Image.open(r.raw)
        return img

    @contextlib.contextmanager
    def __wait_until_finish_loading(
        self, timeout_sec: int, ignore_timeout: bool = False
    ):
        old_page = self.driver.find_element(By.TAG_NAME, "html")
        yield
        try:
            WebDriverWait(self, timeout_sec).until(EC.staleness_of(old_page))
        except TimeoutException as e:
            if not ignore_timeout:
                raise e

    def __login(self) -> bool:
        web_url = self.bot_config.web_url
        account = self.bot_config.account
        password = self.bot_config.password

        assert web_url is not None, "web_url is None"
        assert account is not None, "account is None"
        assert password is not None, "password is None"

        # open target web page
        with self.__wait_until_finish_loading(10):
            self.driver.get(web_url)

        # fetch captcha
        image_element = self.driver.find_element(By.CLASS_NAME, "z-bwcaptcha")
        image_src_value = image_element.get_attribute("src")
        image_url = image_src_value.split(";")[0]

        # extract session id from cookie
        auth_key = "JSESSIONID"
        auth_token = self.driver.get_cookie(auth_key)["value"]

        # get the image
        image = self.__get_image(
            image_url, auth_key, auth_token, timeout_sec=10
        )

        # decode
        decode_str = self.model.predict(image)

        # enter the string
        input_fields = self.driver.find_elements(
            By.CLASS_NAME, "input-body-textbox"
        )
        values = (account, password, decode_str)
        for value, field in zip(values, input_fields):
            field.send_keys(value)

        # press login
        with self.__wait_until_finish_loading(3, ignore_timeout=True):
            self.driver.find_element(By.CLASS_NAME, "z-button-os").click()

        # check whether login succeed
        error_alert_list = self.driver.find_elements(
            By.CLASS_NAME, "z-window-highlighted-cnt"
        )
        if len(error_alert_list) == 0:
            return True
        error_alert = error_alert_list[0]
        error_msg = error_alert.find_element(
            By.CLASS_NAME, "z-label"
        ).get_attribute("innerHTML")
        logger.error("Login failed, reason: %s", error_msg)
        return False

    def login(self) -> bool:
        delay_sec = self.bot_config.delay_sec
        retry_times = self.bot_config.retry_times
        for i in range(retry_times):
            if i > 0:
                logger.info("Delay %d seconds", delay_sec)
                time.sleep(delay_sec)
            logger.info("%d try", i)

            try:
                if self.__login():
                    return True
            except NoSuchElementException:
                logger.error("Error occur !")
            except TimeoutException:
                logger.error("Time ran out !")

        return False

    def refresh(self, timeout_sec: int):
        with self.__wait_until_finish_loading(timeout_sec):
            self.driver.refresh()

    def book(self):
        pass
