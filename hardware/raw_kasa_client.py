# hardware/raw_kasa_client.py
import logging

from kasa import Discover

logger = logging.getLogger(__name__)


class RawKasaClient:
    def __init__(self):
        """
        初始化 KasaDeviceClient，負責與 Kasa 設備進行通信。
        這裡不需要 IP 地址，因為 Discover 將自動尋找設備。
        """
        self._plug = None
        self._strip = None

    _PLUG_ID = 0

    async def _get_device(self):
        try:
            if self._plug is None or self._strip is None:
                all_devices = await Discover.discover()
                self._strip = list(all_devices.values())[0]
                await self._strip.update()
                self._plug = self._strip.children[self._PLUG_ID]
            return self._strip, self._plug
        except:
            self._plug, self._strip = None, None
            logger.error(f"KasaDeviceClient: Failed to discover kasa device")
            raise ConnectionError(f"KasaDeviceClient failed to connect")

    async def turn_on(self):
        """實際發送開啟指令給 Kasa 設備，並更新其狀態。"""
        try:
            strip, plug = await self._get_device()
            await plug.turn_on()
            await strip.update()
        except:
            raise ConnectionError("KasaDeviceClient failed to connect")

    async def turn_off(self):
        """實際發送關閉指令給 Kasa 設備，並更新其狀態。"""
        try:
            strip, plug = await self._get_device()
            await plug.turn_off()
            await strip.update()
        except:
            raise ConnectionError("KasaDeviceClient failed to connect")

    async def is_on(self) -> bool | None:
        """檢查 Kasa 設備是否開啟，返回布林值或 None。"""
        try:
            strip, plug = await self._get_device()
            return plug.is_on
        except:
            raise ConnectionError("KasaDeviceClient failed to connect")
