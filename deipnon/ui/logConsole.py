import logging
import ttkbootstrap as ttk


class LogConsole(ttk.LabelFrame):

    def __init__(self, root, **options):
        ttk.LabelFrame.__init__(self, root, **options)
        self.console = ttk.Text(self, height=10)
        self.console.pack(fill=ttk.BOTH)


class LoggingToGUI(logging.Handler):
    def __init__(self, console: LogConsole):
        logging.Handler.__init__(self)
        self.console = console
        formatter = logging.Formatter(
            "[%(asctime)s][%(levelname)s] %(message)s",
            datefmt="%Y/%m/%d %H:%M:%S",
        )
        self.setFormatter(formatter)

    def emit(self, record):
        formatted_msg = self.format(record)
        formatted_msg = formatted_msg + "\n"
        self.console.configure(state=ttk.NORMAL)
        self.console.insert(ttk.END, formatted_msg)
        self.console.configure(state=ttk.DISABLED)
        self.console.see(ttk.END)


def apply_logging_gui_to_all_logger(log_console: LogConsole):
    package_name = __name__.split(".", maxsplit=1)[0]

    all_my_logger_names = [
        logger_name
        for logger_name in logging.root.manager.loggerDict  # pylint: disable=no-member
        if (
            logger_name.startswith(package_name)
            and logger_name != package_name
        )
    ]

    all_my_logger_names = sorted(all_my_logger_names)
    logger_names_need_to_add = []
    idx = 0
    while idx < len(all_my_logger_names):
        current_name = all_my_logger_names[idx]
        for next_idx in range(idx + 1, len(all_my_logger_names)):
            if not all_my_logger_names[next_idx].startswith(current_name):
                idx = next_idx - 1
                break
        logger_names_need_to_add.append(current_name)
        idx += 1

    for logger_name in logger_names_need_to_add:
        lgr = logging.getLogger(logger_name)
        logging_to_gui_hdl = LoggingToGUI(log_console.console)
        lgr.addHandler(logging_to_gui_hdl)
