import logging
import asyncio
from hardware.thermometer import Thermometer
from hardware.display import DisplayManager
from hardware.power_led import PowerLED
from hardware.kasa_client import KasaClient
from hardware.temp_button_manager import TempButtonManager
from cooker.temp_control_strategy import TemperatureControlStrategy
from cooker.simple_on_off_strategy import SimpleOnOffStrategy
from cooker.two_phase_strategy import TwoPhaseStrategy
from cooker.data_logger import DataLogger
from model.system_status import SystemStatus

logger = logging.getLogger(__name__)


class SousVideController:
    def __init__(self, config: dict):
        self.active = False
        self.thermometer = Thermometer()
        self.display = DisplayManager()
        self.kasa_client = KasaClient()
        self.mode = config.get("mode", "normal")
        self.power_led = PowerLED()
        self.data_logger = DataLogger()
        # self.temp_control_input = TempButtonManager()

        # self.control_strategy: TemperatureControlStrategy = SimpleOnOffStrategy()
        self.control_strategy: TemperatureControlStrategy = TwoPhaseStrategy()
        self.current_plug_state = None  # 輔助LED燈號



        self._status = SystemStatus(
            thermometer=self.thermometer,
            kasa_client=self.kasa_client,
            stragey=self.control_strategy,
            controller=self,
        )

        logger.debug(f"SousVideController initialized with mode={self.mode}")

    def get_system_status(self):
        return self._status

    async def control_led(self):
        if self.active:
            self.power_led.set_heating(self.current_plug_state)
        else:
            self.power_led.turn_off()

    async def on_switch_changed(self, on: bool):
        self.active = on
        if self.mode == "switch_detect":
            logger.info(f"[switch_detect] Switch is now: {'ON' if on else 'OFF'}")
        elif not on:
            logger.info("🔴 Switch turned OFF. Stopping sous-vide process and turning off plug.")
            await self.kasa_client.turn_off()
            self.display.clear()
        else:
            logger.info("🟢 Switch turned ON. System set to active, awaiting temperature control.")

    async def _handle_inactive_state(self):
        """處理舒肥機非活動狀態時的邏輯。"""
        logger.debug("Sous-vide inactive. Tick skipped.")
        await self.kasa_client.turn_off()  # 確保插座關閉
        self.display.clear()  # 清空顯示器

    async def _handle_active_state(self):
        """處理舒肥機活動狀態時的核心溫控邏輯。"""
        try:
            # 1. 讀取溫度
            # temperature = self.thermometer.read_temperature()
            temperature = await asyncio.to_thread(self.thermometer.read_temperature)
            logger.info(f"Current temperature: {temperature:.2f}°C")
            self.display.show_temperature(temperature)

            # 2. 讓溫控策略決定行動
            self.current_plug_state = self.kasa_client.is_on()
            self.data_logger.log(temperature, self.current_plug_state)
            if self.current_plug_state is None:
                logger.warning("Failed to get current plug state, assuming OFF.")
            action_to_take = await self.control_strategy.decide_action(temperature, self.current_plug_state)

            if action_to_take is not None:
                if action_to_take:
                    await self.kasa_client.turn_on()
                else:
                    await self.kasa_client.turn_off()

        except KeyboardInterrupt as e:
            logger.info("KeyboardInterrupt received, stopping sous-vide process.")
            self.display.clear()
            await self.kasa_client.turn_off()
            raise

        except Exception as e:
            logger.error(f"Error during active state handling: {e}", exc_info=True)
            self.display.show_text("Err")
            await self.kasa_client.turn_off()  # 錯誤時保險起見關閉插座

    async def tick(self):
        logger.debug("Tick called in SousVideController.")
        await self.kasa_client.start_updater()  # 確保智能插座的狀態更新任務正在運行
        """主循環中的週期性處理函式。"""
        if not self.active:
            await self._handle_inactive_state()
        else:
            await self._handle_active_state()
        await self.control_led()
