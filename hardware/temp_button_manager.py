# hardware/temp_button_manager.py

import logging
from typing import Callable

from gpiozero import Button
from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class TempButtonManager:
    def __init__(self, on_temp_change: Callable[[float], None]):
        cfg = ConfigManager()
        up_pin = cfg.get_int("gpio.temp_up_switch_pin", default=9)
        down_pin = cfg.get_int("gpio.temp_down_switch_pin", default=11)

        self.up_button = Button(up_pin, pull_up=True)
        self.down_button = Button(down_pin, pull_up=True)

        self.up_button.when_pressed = self.on_temp_up
        self.down_button.when_pressed = self.on_temp_down
        self._callback = on_temp_change

        logger.debug(f"TempUp button initialized on GPIO{up_pin}")
        logger.debug(f"TempDown button initialized on GPIO{down_pin}")

    def on_temp_up(self):
        self._callback(1.0)  # 假設每次按下增加1度

    def on_temp_down(self):
        self._callback(-1.0)  # 假設每次按下減少1度


    def close(self):
        self.up_button.close()
        self.down_button.close()
