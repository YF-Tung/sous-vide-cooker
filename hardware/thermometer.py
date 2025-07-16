import os
import logging
import random
import time
from collections import deque

logger = logging.getLogger(__name__)


class Thermometer:
    """
    使用 DS18B20 感測器從 /sys/bus/w1/devices/28-xxxx/w1_slave 讀取溫度。
    注意：每次讀取會 blocking 最多約 750ms（12-bit 準確度時）。
    """
    BASE_DIR = "/sys/bus/w1/devices"

    def __init__(self):
        self.device_file = None  # lazy init
        self._last_temperature = None  # 用於記錄上次讀取的溫度
        logger.debug("Thermometer initialized (lazy device setup)")
        self._history = deque(maxlen=3600)

    def _find_device_file(self) -> str:
        if not os.path.exists(self.BASE_DIR):
            raise RuntimeError("1-Wire bus directory not found. Did you enable 1-Wire in raspi-config?")

        devices = [d for d in os.listdir(self.BASE_DIR) if d.startswith("28-")]
        if not devices:
            raise RuntimeError("No DS18B20 device found under /sys/bus/w1/devices")

        device_path = os.path.join(self.BASE_DIR, devices[0], "w1_slave")
        return device_path

    def get_last_temperature(self) -> float | None:
        """
        這是在假設溫度計已經被讀取過的情況下，返回最後一次讀取的溫度。
        :return:
        """
        return self._last_temperature

    def _record_temperature(self, temperature: float):
        self._last_temperature = temperature  # 更新最後讀取的溫度
        timestamp = time.time()
        self._history.append((timestamp, temperature))

    def get_history(self):
        """
        回傳 list，每筆是 (timestamp, temperature)
        """
        return list(self._history)

    def read_temperature(self) -> float:
        if not self.device_file:
            self.device_file = self._find_device_file()
            logger.debug(f"Thermometer device file resolved: {self.device_file}")

        try:
            with open(self.device_file, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            raise RuntimeError(f"Failed to read from sensor: {e}")

        if len(lines) < 2 or "YES" not in lines[0]:
            raise RuntimeError("Sensor data not valid")

        try:
            temp_str = lines[1].split("t=")[-1]
            temperature = float(temp_str) / 1000.0
            self._record_temperature(temperature)
            return round(temperature, 2)
        except Exception as e:
            raise RuntimeError(f"Failed to parse temperature: {e}")


class DummyThermometer:
    """
    模擬溫度計，用於不接硬體時的測試。
    每次返回 54 ± 0.5 度的隨機值。
    """

    def __init__(self):
        logger.debug("DummyThermometer initialized")

    def read_temperature(self) -> float:
        return round(54.0 + random.uniform(-0.5, 0.5), 2)