import contextlib
import datetime
import time
import os
from typing import Callable, Optional
from abc import ABC, abstractmethod

import requests
import msgspec
import schedule

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from PIL import Image

from ..config import BotConfig
from ..utils import get_logger
from ..predict import Captcha

logger = get_logger(__name__)


class BotBase(ABC):

    class Ticket(msgspec.Struct):
        id: str
        name: str
        initiator: str
        start_time: datetime.datetime
        end_time: datetime.datetime
        button: WebElement

    def __init__(self, bot_config: BotConfig):
        self.driver = None
        self.model = None
        self.bot_config = bot_config
        self.initial_model()

    def __del__(self):
        if self.driver:
            self.driver.quit()

    def close(self):
        if self.driver:
            self.driver.quit()

    def initial_model(self):
        model_path = self.bot_config.model_path

        assert model_path is not None and os.path.exists(
            model_path
        ), f"model_path ({model_path}) is invalid"

        logger.info("Initial yolo model %s", model_path)
        self.model = Captcha(model_path)

    @abstractmethod
    def initial_browser(self):
        raise NotImplementedError

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
            WebDriverWait(self.driver, timeout_sec).until(
                EC.staleness_of(old_page)
            )
        except TimeoutException as e:
            if not ignore_timeout:
                raise e

    def __wait_and_find_element(
        self,
        element_info: tuple[By, str],
        timeout_sec: int,
        ignore_timeout: bool = False,
    ) -> Optional[WebElement]:
        try:
            return WebDriverWait(
                self.driver, timeout_sec, poll_frequency=0.1
            ).until(EC.visibility_of_element_located(element_info))
        except TimeoutException as e:
            if not ignore_timeout:
                raise e
            return None

    def __try_find_info_msg(
        self, timeout_sec: int
    ) -> Optional[tuple[str, WebElement]]:
        msg_search_data = (
            By.XPATH,
            "//div[contains(@class, 'z-window-highlighted-cnt')]//span[contains(@class, 'z-label')]",
        )
        if timeout_sec > 0:
            info_label = self.__wait_and_find_element(
                msg_search_data,
                timeout_sec,
                ignore_timeout=True,
            )
        else:
            try:
                info_label = self.driver.find_element(*msg_search_data)
            except NoSuchElementException:
                info_label = None

        if info_label is None:
            return None

        info_msg = info_label.get_attribute("innerHTML")
        info_msg_confirm_btn = self.driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'z-window-highlighted-cnt')]//button[contains(@class, 'z-button-os')]",
        )
        return (info_msg, info_msg_confirm_btn)

    def __retry_task(self, func: Callable):
        delay_sec = self.bot_config.delay_sec
        retry_times = self.bot_config.retry_times
        for i in range(retry_times):
            if i > 0:
                logger.info("Delay %d seconds", delay_sec)
                time.sleep(delay_sec)
            logger.info("%d try", i)

            try:
                if func():
                    return True
            except NoSuchElementException as e:
                logger.error("Cannot find the element! %s", e)
            except TimeoutException as e:
                logger.error("Time ran out! %s", e)
            except AssertionError as e:
                logger.error("Assertion: %s", e)

        return False

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
            field.clear()
            field.send_keys(value)

        # press login
        with self.__wait_until_finish_loading(10, ignore_timeout=True):
            self.driver.find_element(By.CLASS_NAME, "z-button-os").click()

        # check whether login succeed
        info_data = self.__try_find_info_msg(timeout_sec=0)
        if info_data is None:
            return True

        info_msg, info_confirm_btn = info_data
        info_confirm_btn.click()
        logger.error("Login failed, reason: %s", info_msg)
        return False

    def login(self) -> bool:
        return self.__retry_task(self.__login)

    def refresh(self, timeout_sec: int):
        with self.__wait_until_finish_loading(timeout_sec):
            self.driver.refresh()

    def __book(self):
        ticket_name = self.bot_config.ticket_name
        ticket_item_name = self.bot_config.ticket_item_name

        self.refresh(20)
        table = self.__wait_and_find_element(
            (
                By.XPATH,
                "//div[@class='z-tabpanel' and not(contains(@style,'display:none'))]//div[@class='z-grid-body']//tbody[contains(@class, 'z-rows')]",
            ),
            timeout_sec=5,
        )
        rows = table.find_elements(
            By.XPATH, "./tr[contains(@class, 'gridcss z-row')]"
        )
        rows = list(filter(lambda row: len(row.text) > 0, rows))
        row_cols = list(
            map(
                lambda row: row.find_elements(
                    By.XPATH, "./td[@class='z-row-inner']"
                ),
                rows,
            )
        )

        DATETIME_FORMAT = r"%Y/%m/%d %H:%M"
        tickets = list(
            map(
                lambda cols: self.Ticket(
                    id=str(cols[0].text),
                    name=str(cols[1].text),
                    initiator=str(cols[2].text),
                    start_time=datetime.datetime.strptime(
                        str(cols[3].text).split("~", maxsplit=1)[0].strip(),
                        DATETIME_FORMAT,
                    ),
                    end_time=datetime.datetime.strptime(
                        str(cols[3].text).split("~")[1].strip(),
                        DATETIME_FORMAT,
                    ),
                    button=cols[4].find_element(By.TAG_NAME, "button"),
                ),
                row_cols,
            )
        )
        logger.info("Ticket:\n%s", "\n".join(map(str, tickets)))

        # find the target ticket
        for ticket in tickets:
            if ticket_name in ticket.name:
                ticket.button.click()
                logger.info("Plan to sign up %s", ticket)
                break

        # get pop window
        pop_window = self.__wait_and_find_element(
            (By.XPATH, "//div[contains(@class, 'z-window-popup')]"),
            timeout_sec=5,
        )

        # check if there is an error
        info_data = self.__try_find_info_msg(timeout_sec=0)
        if info_data is not None:
            info_msg, info_confirm_btn = info_data
            info_confirm_btn.click()
            logger.error("Book failed, reason: %s", info_msg)
            return False

        # click list
        select_bar = pop_window.find_element(
            By.XPATH, "//input[contains(@class, 'z-combobox-inp')]"
        )
        select_bar.click()

        # get list
        select_list = self.__wait_and_find_element(
            (By.XPATH, "//div[contains(@class, 'z-combobox-pp')]"),
            timeout_sec=5,
        )
        select_items = select_list.find_elements(
            By.XPATH, "//tr[@class='z-comboitem']"
        )

        # find the target item
        found = False
        for item in select_items:
            if ticket_item_name in item.text:
                item.click()
                found = True
        assert found, f"Cannot find the target item ({ticket_item_name})"

        # send submit
        submit_btn = pop_window.find_element(
            By.XPATH,
            "//button[contains(@class, 'cssbtn1') and contains(@class, 'z-button-os')]",
        )
        submit_btn.click()

        # get the result
        info_data = self.__try_find_info_msg(timeout_sec=0)
        if info_data is not None:
            info_msg, info_confirm_btn = info_data
            info_confirm_btn.click()
            logger.error("Book result: %s", info_msg)
            return True

        logger.error("Book failed")
        return False

    def book(self) -> bool:
        return self.__retry_task(self.__book)

    def wait_for_time_to_run_once(self):
        start_time = self.bot_config.start_time
        pre_login_time = self.bot_config.pre_login_time

        def schedule_wrapper(func):
            def wrapper():
                func()
                return schedule.CancelJob

            return wrapper

        def login_routine():
            self.initial_browser()
            self.login()

        schedule.every().day.at(pre_login_time).do(
            schedule_wrapper(login_routine)
        )
        schedule.every().day.at(start_time).do(schedule_wrapper(self.book))

        logger.info("Start working...")

        while True:
            schedule.run_pending()
            if len(schedule.get_jobs()) > 0:
                time.sleep(1)
            else:
                self.close()
                break
