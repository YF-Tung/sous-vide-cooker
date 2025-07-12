import asyncio
import logging
import yaml
from hardware.switch import SwitchInputManager
from cooker.controller import SousVideController
from logger_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)



def load_config():
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to load config.yaml: {e}")
        raise


async def main():
    config = load_config()
    polling_interval = config.get("polling_interval")

    controller = SousVideController(config=config)
    switch_input = SwitchInputManager()
    last_switch_state = None

    loop = asyncio.get_running_loop()
    while True:
        ts = loop.time()
        switch_state = switch_input.is_switch_on()

        # If the switch is off, use a shorter polling interval, since nothing to wait for.
        actual_polling_interval = polling_interval if switch_state else 0.2

        if switch_state != last_switch_state:
            await controller.on_switch_changed(switch_state)
            last_switch_state = switch_state

        await controller.tick()
        remaining_time = actual_polling_interval - (loop.time() - ts)
        if remaining_time < 0.1:
            logger.warning(f"Tick took too long, see logs for details. Remaining time: {remaining_time:.2f}s")
            remaining_time = 0.1
        await asyncio.sleep(remaining_time)


if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.set_debug(True)
    main_loop.slow_callback_duration = 0.1  # 設定慢回調的閾值為 100ms
    main_loop.run_until_complete(main())
    main_loop.close()
