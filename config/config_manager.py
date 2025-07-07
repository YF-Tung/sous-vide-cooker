# config/config_manager.py
import yaml
from pathlib import Path
from threading import Lock

class ConfigManager:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._load_config()
            return cls._instance

    def _load_config(self):
        config_path = Path(__file__).resolve().parent.parent / "config.yaml"
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[WARN] Failed to load config.yaml: {e}")
            self._config = {}

    def get_string(self, key, default=""):
        return str(self._get_nested(key, default))

    def get_int(self, key, default=0):
        try:
            return int(self._get_nested(key, default))
        except (ValueError, TypeError):
            return default

    def get_float(self, key, default=0.0):
        try:
            return float(self._get_nested(key, default))
        except (ValueError, TypeError):
            return default

    def get_bool(self, key, default=False):
        value = self._get_nested(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("1", "true", "yes")

    def get_dict(self, key):
        return self._get_nested(key, {})

    def _get_nested(self, dotted_key, default):
        keys = dotted_key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value