from deipnon.driver import WEB_DRIVER_TYPE
from deipnon.config import BotConfig
from deipnon.utils import get_logger
from deipnon.bot.bots import ChromeBot, EdgeBot, FirefoxBot
from deipnon.bot.botBase import BotBase


logger = get_logger(__name__)


class BotFactory:

    @classmethod
    def new_bot(cls, bot_config: BotConfig) -> BotBase:
        bot_type = bot_config.web_driver_type
        logger.info("Use browser %s", bot_type)
        match bot_type:
            case WEB_DRIVER_TYPE.CHROME:
                return ChromeBot(bot_config)
            case WEB_DRIVER_TYPE.EDGE:
                return EdgeBot(bot_config)
            case WEB_DRIVER_TYPE.FIREFOX:
                return FirefoxBot(bot_config)
            case _:
                raise RuntimeError(f"Unknown Web Driver Type {bot_type}")
