# hardware/temp_button_manager.py

import logging
from gpiozero import Button
from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class TempButtonManager:
    def __init__(self):
        cfg = ConfigManager()
        up_pin = cfg.get_int("gpio.temp_up_switch_pin", default=9)
        down_pin = cfg.get_int("gpio.temp_down_switch_pin", default=11)

        self.up_button = Button(up_pin, pull_up=True)
        self.down_button = Button(down_pin, pull_up=True)

        self.up_button.when_pressed = self.on_temp_up
        self.down_button.when_pressed = self.on_temp_down

        logger.debug(f"TempUp button initialized on GPIO{up_pin}")
        logger.debug(f"TempDown button initialized on GPIO{down_pin}")

    def on_temp_up(self):
        logger.info("Temp UP button pressed (not implemented yet)")

    def on_temp_down(self):
        logger.info("Temp DOWN button pressed (not implemented yet)")

    def close(self):
        self.up_button.close()
        self.down_button.close()
