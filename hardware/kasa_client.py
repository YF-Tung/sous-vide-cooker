# hardware/kasa_client.py

import asyncio
import logging
import time
from hardware.raw_kasa_client import RawKasaClient

logger = logging.getLogger(__name__)


class KasaClient:
    """
    用於控制 TP-Link Kasa 智慧插座的 Class。
    內部維護目標狀態，並在背景任務中按步調執行操作，包含頻率限制。
    不直接與 Kasa API 交互，而是透過 KasaDeviceClient。
    """

    def __init__(self, min_op_interval: float = 1.0, update_interval: float = 1.0):
        """
        初始化 KasaSmartPlug。

        Args:
            min_op_interval (float): 最小操作間隔 (秒)，避免頻繁開關。
            update_interval (float): 背景任務更新頻率 (秒)。
        """
        # 不再接收 ip_address 參數
        self._device_client = RawKasaClient()
        self._min_op_interval = min_op_interval
        self._last_op_time = 0.0

        self._pending_state: bool | None = None
        self._current_physical_state: bool | None = None

        self._update_interval = update_interval

        self._updater_is_running = False
        self._state_updater_task = None
        #self._state_updater_task = asyncio.create_task(self._run_state_updater())
        # 日誌訊息中不再包含 IP，因為 KasaSmartPlug 不關心它了
        logger.info(f"KasaSmartPlug initialized. Min operation interval: {min_op_interval}s")

    async def _run_state_updater(self):
        loop = asyncio.get_running_loop()
        logger.info("跑起來！")
        """
        在背景持續運行，負責檢查狀態、執行插座操作並處理頻率限制。
        """
        while True:
            logger.info("KasaSmartPlug: Running state updater task.")
            try:
                # 獲取當前實際的物理狀態
                # 這裡依賴 _KasaDeviceClient 處理連接狀態和錯誤
                self._current_physical_state = await self._device_client.is_on()

                if self._pending_state is not None:
                    if self._pending_state == self._current_physical_state:
                        # 如果待處理狀態與當前物理狀態一致，則不需要執行操作
                        logger.debug(f"KasaSmartPlug: No action needed. Current state is {self._current_physical_state}.")
                        self._pending_state = None
                    else:
                        # 如果有待處理的狀態，且與當前物理狀態不一致，則執行操作
                        current_time = loop.time()  # todo
                        if current_time - self._last_op_time >= self._min_op_interval:
                            if self._pending_state:
                                logger.info(f"KasaSmartPlug: Executing scheduled turn_on.")
                                await self._device_client.turn_on()
                            else:
                                logger.info(f"KasaSmartPlug: Executing scheduled turn_off.")
                                await self._device_client.turn_off()

                            self._last_op_time = current_time  # todo
                            self._current_physical_state = self._pending_state
                            self._pending_state = None  # 清除待處理狀態
                        else:
                            logger.debug(
                                f"KasaSmartPlug: Waiting {self._min_op_interval - (current_time - self._last_op_time):.1f}s before executing {self._pending_state}.")

            except ConnectionError:
                logger.warning("KasaSmartPlug: Device client not connected. Retrying connection in background.")
                self._current_physical_state = None  # 連接問題導致狀態未知
                # KasaDeviceClient 內部會處理連接重試，這裡只要等待即可
            except Exception as e:
                logger.error(f"Error in KasaSmartPlug state updater: {e}", exc_info=True)
                self._current_physical_state = None

            logger.debug("Finished state update cycle.")
            await asyncio.sleep(self._update_interval)

    async def turn_on(self) -> bool:
        """
        設定智慧插座的目標狀態為開啟。此操作非阻塞，只是設定意圖。
        """
        if self._pending_state == True:
            logger.debug(f"KasaSmartPlug: Already intended ON. No change.")
            return

        if self._pending_state == False:
            logger.warning(
                f"KasaSmartPlug: Conflicting command received. Intended OFF, now setting to ON.")

        self._pending_state = True
        logger.info(f"KasaSmartPlug: Enqueued turn_on. Background task will handle execution.")

    async def turn_off(self) -> bool:
        """
        設定智慧插座的目標狀態為關閉。此操作非阻塞，只是設定意圖。
        """
        if self._pending_state == False:
            logger.debug(f"KasaSmartPlug: Already intended OFF. No change.")
            return

        if self._pending_state == True:
            logger.warning(
                f"KasaSmartPlug: Conflicting command received. Intended ON, now setting to OFF.")

        self._pending_state = False
        logger.info(f"KasaSmartPlug: Enqueued turn_off. Background task will handle execution.")

    def is_on(self) -> bool | None:
        """
        返回智慧插座的當前實際狀態。
        這返回的是內部背景任務最近從物理設備獲取的狀態。
        """
        return self._current_physical_state

    async def start_updater(self):
        """
        確保背景任務已啟動並正在運行。
        如果未啟動，則開始新的任務。
        """
        if not self._updater_is_running:
            logger.info("KasaSmartPlug: Starting state updater task.")
            self._updater_is_running = True
            self._state_updater_task = asyncio.create_task(self._run_state_updater())
