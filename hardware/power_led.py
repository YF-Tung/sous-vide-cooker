# hardware/power_led.py

import logging
import asyncio
from gpiozero import LED
from config.config_manager import ConfigManager
import time

logger = logging.getLogger(__name__)
cfg = ConfigManager()


class PowerLED:
    """
    控制加熱狀態指示燈：
    - heating=True  → LED 恆亮
    - heating=False → LED 閃爍（每秒兩次）
    """

    def __init__(self):
        pin = cfg.get_int("power_led", default=10)  # 實體 Pin 19，GPIO10
        self.led = LED(pin)
        self._heating = False
        self._blink_task = None
        logger.debug(f"LED initialized on GPIO{pin}")

    def turn_on(self):
        """點亮 LED（無閃爍，恆亮）"""
        self._stop_blinking()
        self.led.on()
        logger.debug("LED turned ON")

    def turn_off(self):
        """關閉 LED"""
        self._stop_blinking()
        self.led.off()
        logger.debug("LED turned OFF")

    def set_heating(self, heating: bool):
        """設定加熱狀態，切換為恆亮或閃爍模式"""
        self._heating = heating
        if heating:
            self._stop_blinking()
            self.led.on()
            logger.debug("LED ON (heating)")
        else:
            if self._blink_task is None or self._blink_task.done():
                self._blink_task = asyncio.create_task(self._blink())
            logger.debug("LED BLINK (not heating)")

    async def _blink(self):
        """背景閃爍任務：每秒兩次，使用明確 on/off"""
        try:
            interval = 0.25  # 250ms
            state = False  # 初始狀態：off
            next_time = time.monotonic()
            while not self._heating:
                if state:
                    self.led.on()
                else:
                    self.led.off()
                state = not state  # 交替開關
                next_time += interval
                sleep_duration = max(0, next_time - time.monotonic())
                await asyncio.sleep(sleep_duration)
        except asyncio.CancelledError:
            self.led.off()

    def _stop_blinking(self):
        """停止閃爍任務（如果有）"""
        if self._blink_task and not self._blink_task.done():
            self._blink_task.cancel()
            logger.debug("Stopped blinking task")