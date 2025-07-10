# cooker/simple_on_off_strategy.py
import logging
import time

from cooker.temp_control_strategy import TemperatureControlStrategy

logger = logging.getLogger(__name__)


class TwoPhaseStrategy(TemperatureControlStrategy):
    """
    TwoPhaseStrategy：兩階段溫控策略。
    溫度小於目標溫度五度以上：全力加熱
    溫度小於目標五度以內：每次加熱十秒後強制斷開
    溫度高於目標溫度：停止加熱。
    """

    def __init__(self, target_temperature: float = 63.0):
        self.target_temperature = target_temperature

        self._last_observed_state: bool | None = None  # 上次觀察到的插座狀態
        self._last_actual_change_time = 0.0  # 上次實際改變插座狀態的時間
        self._min_change_interval = 10.0  # 最小操作間隔 (秒)

    def _ok_to_change(self) -> bool:
        time_since_last_change = time.time() - self._last_actual_change_time
        logger.debug(f"Time since last change: {time_since_last_change:.2f} seconds, ")
        return time_since_last_change >= self._min_change_interval

    def _update_state(self, current_plug_is_on: bool):
        logger.debug(f"Updating state: Current plug is {'ON' if current_plug_is_on else 'OFF'}")
        if self._last_observed_state is None or self._last_observed_state != current_plug_is_on:
            logger.debug("status" + str(self._last_observed_state) + str(current_plug_is_on))
            logger.debug(f"State change detected: {'ON' if current_plug_is_on else 'OFF'}")
            self._last_actual_change_time = time.time()
        self._last_observed_state = current_plug_is_on

    async def decide_action(self, current_temperature: float, current_plug_is_on: bool) -> bool | None:
        logger.debug(
            f"TwoPhase: Current temperature: {current_temperature:.2f}°C, Current plug state: {current_plug_is_on}")
        self._update_state(current_plug_is_on)
        desired_state: bool | None = None  # 預期的插座狀態
        if not self._ok_to_change():
            return None
        if current_temperature < self.target_temperature - 5:
            logger.info(f"當前溫度 {current_temperature:.2f}°C 低於目標 {self.target_temperature:.2f}°C，建議開啟插座。")
            desired_state = True  # 太冷，希望開啟
        elif self.target_temperature - 5 <= current_temperature < self.target_temperature:
            # 已滿足最低秒數，馬上中止
            if current_plug_is_on:
                logger.info(f"當前溫度 {current_temperature:.2f}°C 接近目標 {self.target_temperature:.2f}°C，建議關閉。")
                desired_state = False
            else:
                logger.info(f"當前溫度 {current_temperature:.2f}°C 接近目標 {self.target_temperature:.2f}°C，建議開啟插座。")
                desired_state = True
        elif current_temperature >= self.target_temperature:
            logger.info(f"當前溫度 {current_temperature:.2f}°C 高於目標 {self.target_temperature:.2f}°C，建議關閉插座。")
            desired_state = False  # 太熱，希望關閉

        return desired_state
