import logging
from gpiozero import Button
from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

cfg = ConfigManager()
pin = cfg.get_int("gpio.switch_input_pin", default=17)

# 啟用內建 pull-up（開關導通即接地）
switch = Button(pin, pull_up=True)


def is_switch_on() -> bool:
    """
    回傳 True 表示開關導通（接地） => 我們視為「ON」
    """
    state = switch.is_pressed
    logger.debug(f"Switch pressed: {state}")
    return state