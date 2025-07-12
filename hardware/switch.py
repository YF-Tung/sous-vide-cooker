# hardware/switch_input_manager.py

import logging
from gpiozero import Button
from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class SwitchInputManager:
    def __init__(self):
        cfg = ConfigManager()
        pin = cfg.get_int("gpio.switch_input_pin", default=17)
        self.switch = Button(pin, pull_up=True)
        logger.debug(f"Main switch initialized on GPIO{pin}")

    def is_switch_on(self) -> bool:
        return self.switch.is_pressed

    def close(self):
        self.switch.close()
