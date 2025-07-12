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
        self.backup_count = 5
        self.max_bytes = 1024 * 1024 * 5  # 每個檔案最大 5MB

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
        try:
            # rotate if size too big
            if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > self.max_bytes:
                self._rotate_file()
        except Exception as e:
            logger.warning(f"Failed to rotate log file: {e}")

        if self._buffer:
            self._flush()

    def _rotate_file(self):
        # 關掉現有 buffer（防止 race condition）
        self._flush()

        # Rotate 舊檔案（最多保留 N 個）
        for i in reversed(range(1, self.backup_count)):
            src = f"{self.filepath}.{i}"
            dst = f"{self.filepath}.{i + 1}"
            if os.path.exists(src):
                os.rename(src, dst)

        # 原始檔案改名成 .1
        if os.path.exists(self.filepath):
            os.rename(self.filepath, f"{self.filepath}.1")
