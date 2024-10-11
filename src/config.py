import msgspec
import os


class BotConfig(msgspec.Struct):
    """Config for Bot"""

    web_url: str
    account: str
    password: str

    ticket_name: str
    ticket_item_name: str

    start_time: str
    pre_login_time: str

    delay_sec: int = 0
    retry_times: int = 5
    headless: bool = True
    web_driver_path: str = "./chrome-win64/chrome.exe"
    model_path: str = "./models/yolo11m_fake_5000_real_550.pt"
    proxy_server: str = ""


def read_from_toml_file(toml_path: str) -> BotConfig:
    """Read bot config from toml file"""
    assert toml_path is not None and os.path.exists(
        toml_path
    ), f"toml_path ({toml_path}) is invalid"

    with open(toml_path, "r", encoding="utf-8") as f:
        return msgspec.toml.decode(f.read(), type=BotConfig)


def write_to_toml_file(toml_path: str, config: BotConfig) -> None:
    """Write bot config to toml file"""
    assert toml_path is not None and isinstance(
        toml_path, str
    ), f"toml_path ({toml_path}) is invalid"

    with open(toml_path, "wb") as f:
        f.write(msgspec.toml.encode(config))
