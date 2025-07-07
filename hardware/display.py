# hardware/display.py

import logging
import tm1637
from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)
cfg = ConfigManager()


class DisplayManager:
    def __init__(self):
        clk_pin = cfg.get_int("display_clk_pin", default=22)
        dio_pin = cfg.get_int("display_dio_pin", default=27)

        # 明確指定 gpiochip，根據你環境是 /dev/gpiochip4
        self.display = tm1637.TM1637(clk=clk_pin, dio=dio_pin, chip_path="/dev/gpiochip4")

        logger.debug(f"TM1637 initialized on CLK={clk_pin}, DIO={dio_pin}")

    def show_temperature(self, temp_c: float):
        """顯示攝氏溫度（支援小數點，0~99.9°C）"""
        try:
            if 0.0 <= temp_c < 100.0:
                self.display.temperature_decimal(temp_c)
            else:
                self.display.show("Err")
        except Exception as e:
            logger.error(f"Failed to display temperature: {e}")
            self.display.show("Err")

    def show_text(self, text: str):
        """顯示 4 碼文字（過長自動截斷）"""
        try:
            self.display.show(text[:4])
        except Exception as e:
            logger.error(f"Failed to display text '{text}': {e}")
            self.display.show("Err")

    def clear(self):
        """清除顯示"""
        try:
            self.display.write([0, 0, 0, 0])
        except Exception as e:
            logger.error(f"Failed to clear display: {e}")