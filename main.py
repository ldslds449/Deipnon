from src.bot import Bot
from src.utils import get_config_file_path
from src.config import read_from_toml_file, write_to_toml_file

if __name__ == "__main__":
    config_path = get_config_file_path()
    config = read_from_toml_file(config_path)

    bot = Bot(config)
    bot.login()
    bot.book()

    write_to_toml_file(config_path, config)
