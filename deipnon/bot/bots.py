from selenium import webdriver

from deipnon.bot.botBase import BotBase


class ChromeBot(BotBase):
    def __init__(self, bot_config):
        super().__init__(bot_config)
        self.driver = None

    def initial_browser(self):
        web_driver_path, proxy_server, headless = (
            self.bot_config.web_driver_path,
            self.bot_config.proxy_server,
            self.bot_config.headless,
        )

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


class EdgeBot(BotBase):
    def __init__(self, bot_config):
        super().__init__(bot_config)
        self.driver = None

    def initial_browser(self):
        web_driver_path, proxy_server, headless = (
            self.bot_config.web_driver_path,
            self.bot_config.proxy_server,
            self.bot_config.headless,
        )

        service = webdriver.EdgeService(executable_path=web_driver_path)
        option = webdriver.EdgeOptions()
        option.add_argument("--disable-gpu")
        if headless:
            option.add_argument("--headless=new")
        # https://stackoverflow.com/questions/65080685/usb-usb-device-handle-win-cc1020-failed-to-read-descriptor-from-node-connectio
        option.add_experimental_option("excludeSwitches", ["enable-logging"])

        if proxy_server:
            option.add_argument(f"--proxy-server={proxy_server}")
        self.driver = webdriver.Edge(service=service, options=option)


class FirefoxBot(BotBase):
    def __init__(self, bot_config):
        super().__init__(bot_config)
        self.driver = None

    def initial_browser(self):
        web_driver_path, proxy_server, headless = (
            self.bot_config.web_driver_path,
            self.bot_config.proxy_server,
            self.bot_config.headless,
        )

        service = webdriver.FirefoxService(executable_path=web_driver_path)
        option = webdriver.FirefoxOptions()
        option.add_argument("--disable-gpu")
        if headless:
            option.add_argument("--headless")

        if proxy_server:
            option.add_argument(f"--proxy-server={proxy_server}")
        self.driver = webdriver.Firefox(service=service, options=option)
