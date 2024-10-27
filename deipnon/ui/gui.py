import time
import threading

import schedule
import ttkbootstrap as ttk
from ttkbootstrap.constants import LEFT

from deipnon.utils import get_config_file_path, get_logger
from deipnon.config import read_from_toml_file, write_to_toml_file
from deipnon.driver import check_webdriver, download_webdriver
from deipnon.bot.botFactory import BotFactory
from deipnon.ui.logConsole import LogConsole, apply_logging_gui_to_all_logger

logger = get_logger(__name__)


class GUI:
    def __init__(self):
        self.config_path = None
        self.config = None
        self.bot = None
        self.root = None
        self.book_btn = None
        self.schedule_btn = None

    def show(self):
        self.root = ttk.Window(themename="darkly")

        log_console = LogConsole(self.root, text="Log")
        log_console.grid(row=0, column=0, columnspan=2)
        apply_logging_gui_to_all_logger(log_console)

        self.book_btn = ttk.Button(
            self.root,
            text="Book Now",
            bootstyle="primary",
            command=self.__run_book_tasks,
        )
        self.book_btn.grid(row=1, column=0)

        self.schedule_btn = ttk.Button(
            self.root,
            text="Schedule",
            bootstyle="primary",
            command=self.__run_schedule_tasks,
        )
        self.schedule_btn.grid(row=1, column=1)

        self.__read_config()
        self.__check_webdriver()
        self.__initial_bot()

        self.root.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self.root.mainloop()

    def __on_closing(self):
        self.bot.close()
        self.root.destroy()

    def __read_config(self):
        self.config_path = get_config_file_path()
        self.config = read_from_toml_file(self.config_path)

    def __check_webdriver(self):
        if not check_webdriver(self.config.web_driver_path):
            self.config.web_driver_path = download_webdriver(
                self.config.web_driver_type, self.config.web_driver_path
            )

    def __initial_bot(self):
        self.bot = BotFactory.new_bot(self.config)

    def __update_config(self):
        write_to_toml_file(self.config_path, self.config)

    def __run_book_tasks(self):
        self.book_btn.state((ttk.DISABLED, ))
        self.schedule_btn.state((ttk.DISABLED, ))

        def tasks():
            logger.info("Start working...")
            self.bot.initial_browser()
            self.bot.login()
            self.bot.book()
            self.book_btn.state((ttk.NORMAL, ))
            self.schedule_btn.state((ttk.NORMAL, ))

        t = threading.Thread(target=tasks, daemon=True)
        t.start()

    def __run_schedule_tasks(self):
        self.book_btn.state((ttk.DISABLED, ))
        self.schedule_btn.state((ttk.DISABLED, ))

        start_time = self.config.start_time
        pre_login_time = self.config.pre_login_time
        logger.info("Login time: %s", pre_login_time)
        logger.info("Book time: %s", start_time)

        def schedule_wrapper(func):
            def wrapper():
                func()
                return schedule.CancelJob

            return wrapper

        def login_routine():
            self.bot.initial_browser()
            self.bot.login()

        schedule.every().day.at(pre_login_time).do(
            schedule_wrapper(login_routine)
        )
        schedule.every().day.at(start_time).do(schedule_wrapper(self.bot.book))

        def tasks():
            logger.info("Start working...")
            while True:
                schedule.run_pending()
                if len(schedule.get_jobs()) > 0:
                    time.sleep(0.1)
                else:
                    self.bot.close()
                    break
            self.book_btn.state((ttk.NORMAL, ))
            self.schedule_btn.state((ttk.NORMAL, ))

        t = threading.Thread(target=tasks, daemon=True)
        t.start()
