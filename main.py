import asyncio
import time
import logging
import yaml

from logger_config import setup_logging
setup_logging()

from hardware.switch import is_switch_on
from cooker.controller import SousVideController

logger = logging.getLogger(__name__)


def load_config():
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to load config.yaml: {e}")
        return {"mode": "cook", "polling_interval": 1.0}


async def main():
    config = load_config()
    polling_interval = config.get("polling_interval", 2.0)

    controller = SousVideController(config=config)
    last_switch_state = None

    while True:
        ts = time.time()
        switch_state = is_switch_on()

        if switch_state != last_switch_state:
            await controller.on_switch_changed(switch_state)
            last_switch_state = switch_state

        await controller.tick()
        remaining_time = max(polling_interval - (time.time() - ts), 0.1)
        await asyncio.sleep(remaining_time)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.slow_callback_duration = 0.1  # 設定慢回調的閾值為 100ms
    loop.run_until_complete(main())
    loop.close()
