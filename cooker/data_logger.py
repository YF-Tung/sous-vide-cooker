# services/data_logger.py

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataLogger:
    def __init__(self, filepath: str = "logs/heating_log.tsv", buffer_size: int = 30):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.filepath = filepath
        self._buffer = []
        self._buffer_size = buffer_size

        # 若檔案不存在，寫入表頭
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                f.write("timestamp\ttemperature\theating\n")

    def log(self, temperature: float, heating: bool):
        timestamp = datetime.now().isoformat()
        line = f"{timestamp}\t{temperature:.2f}\t{int(heating)}\n"
        self._buffer.append(line)

        if len(self._buffer) >= self._buffer_size:
            self._flush()

    def _flush(self):
        try:
            with open(self.filepath, "a") as f:
                f.writelines(self._buffer)
                f.flush()
            logger.debug(f"Flushed {len(self._buffer)} log lines to file.")
        except Exception as e:
            logger.warning(f"Failed to flush log buffer: {e}")
        finally:
            self._buffer.clear()

    def flush(self):
        """外部強制 flush 緩衝區。可在程式結束時呼叫。"""
        if self._buffer:
            self._flush()