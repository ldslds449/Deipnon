from src.bot import Bot
from src.utils import get_config_file_path
from src.driver import check_webdriver, download_webdriver
from src.config import read_from_toml_file, write_to_toml_file

if __name__ == "__main__":
    config_path = get_config_file_path()
    config = read_from_toml_file(config_path)

    if not check_webdriver(config.web_driver_path):
        config.web_driver_path = download_webdriver(
            config.web_driver_type, config.web_driver_path
        )

    bot = Bot(config)
    bot.wait_for_time_to_run_once()

    write_to_toml_file(config_path, config)
