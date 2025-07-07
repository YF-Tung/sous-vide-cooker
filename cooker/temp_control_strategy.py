# cooker/temp_control_strategy.py
import abc


class TemperatureControlStrategy(abc.ABC):
    @abc.abstractmethod
    async def decide_action(self, current_temperature: float, current_plug_is_on: bool) -> bool | None:
        pass
