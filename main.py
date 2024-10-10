import os
import sys
from src.bot import Bot
from src.config import read_from_toml_file, write_to_toml_file


def get_config_file_path():
    """find out config file path from arguments and environment variables or using default values"""
    if len(sys.argv) > 1:
        return sys.argv[-1]
    return os.environ.get("CONFIG_PATH", "config.toml")


if __name__ == "__main__":
    config_path = get_config_file_path()
    config = read_from_toml_file(config_path)

    bot = Bot(config)
    bot.login()

    write_to_toml_file(config_path, config)
