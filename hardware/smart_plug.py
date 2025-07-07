# hardware/smart_plug.py

import asyncio
import logging
import time
from hardware.kasa_device_client import KasaDeviceClient

logger = logging.getLogger(__name__)


class KasaSmartPlug:
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
        self._device_client = KasaDeviceClient()  # ⬅ 直接實例化，不傳 IP
        self._min_op_interval = min_op_interval
        self._last_op_time = 0.0

        self._intended_state: bool | None = None
        self._current_physical_state: bool | None = None

        self._update_interval = update_interval

        self._updater_is_running = False
        self._state_updater_task = None
        #self._state_updater_task = asyncio.create_task(self._run_state_updater())
        # 日誌訊息中不再包含 IP，因為 KasaSmartPlug 不關心它了
        logger.info(f"KasaSmartPlug initialized. Min operation interval: {min_op_interval}s")

    async def start(self):
        if self._updater_is_running is False:
            logger.info("KasaSmartPlug: Starting state updater task.")
            self._updater_is_running = True
            self._state_updater_task = asyncio.create_task(self._run_state_updater())

    async def _run_state_updater(self):
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

                if self._intended_state is not None and self._intended_state != self._current_physical_state:
                    current_time = time.time()
                    if current_time - self._last_op_time >= self._min_op_interval:
                        if self._intended_state:
                            logger.info(f"KasaSmartPlug: Executing scheduled turn_on.")
                            await self._device_client.turn_on()
                        else:
                            logger.info(f"KasaSmartPlug: Executing scheduled turn_off.")
                            await self._device_client.turn_off()

                        self._last_op_time = current_time
                        self._current_physical_state = self._intended_state
                    else:
                        logger.debug(
                            f"KasaSmartPlug: Waiting {self._min_op_interval - (current_time - self._last_op_time):.1f}s before executing {self._intended_state}.")
                elif self._intended_state == self._current_physical_state:
                    logger.debug(
                        f"KasaSmartPlug: Intended state matches physical state ({'ON' if self._intended_state else 'OFF'}). No action needed.")

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
        if self._intended_state == True:
            logger.debug(f"KasaSmartPlug: Already intended ON. No change.")
            return True

        if self._intended_state == False:
            logger.warning(
                f"KasaSmartPlug: Conflicting command received. Intended OFF, now setting to ON.")

        self._intended_state = True
        logger.info(f"KasaSmartPlug: Enqueued turn_on. Background task will handle execution.")
        return True

    async def turn_off(self) -> bool:
        """
        設定智慧插座的目標狀態為關閉。此操作非阻塞，只是設定意圖。
        """
        if self._intended_state == False:
            logger.debug(f"KasaSmartPlug: Already intended OFF. No change.")
            return True

        if self._intended_state == True:
            logger.warning(
                f"KasaSmartPlug: Conflicting command received. Intended ON, now setting to OFF.")

        self._intended_state = False
        logger.info(f"KasaSmartPlug: Enqueued turn_off. Background task will handle execution.")
        return True

    async def is_on(self) -> bool | None:
        """
        返回智慧插座的當前實際狀態。
        這返回的是內部背景任務最近從物理設備獲取的狀態。
        """
        #if not self._updater_is_running:
        #    logger.info("KasaSmartPlug: Starting state updater task.")
        #    self._updater_is_running = True
        #    self._state_updater_task = asyncio.create_task(self._run_state_updater())
        return self._current_physical_state

    async def ensure_started(self):
        """
        確保背景任務已啟動並正在運行。
        如果未啟動，則開始新的任務。
        """
        if not self._updater_is_running:
            logger.info("KasaSmartPlug: Starting state updater task.")
            self._updater_is_running = True
            self._state_updater_task = asyncio.create_task(self._run_state_updater())



# 範例使用方式
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


    # Mock KasaDeviceClient 仍然需要，因為你實際運行這個文件時 KasaDeviceClient 內部可能還沒設實際 IP
    class MockKasaDeviceClient:
        def __init__(self):  # 不再接收 IP
            self._mock_state = False
            self._connected = False
            logger.info("MockKasaDeviceClient initialized (no IP).")

        async def connect(self):
            if not self._connected:
                logger.info("MockKasaDeviceClient: Simulating connection.")
                await asyncio.sleep(0.5)
                self._connected = True
            return self._connected

        async def turn_on(self):
            if not self._connected: raise ConnectionError("Mock not connected")
            logger.info("MockKasaDeviceClient: Simulating actual ON command.")
            await asyncio.sleep(0.2)
            self._mock_state = True
            return True

        async def turn_off(self):
            if not self._connected: raise ConnectionError("Mock not connected")
            logger.info("MockKasaDeviceClient: Simulating actual OFF command.")
            await asyncio.sleep(0.2)
            self._mock_state = False
            return True

        async def is_on(self):
            if not self._connected: raise ConnectionError("Mock not connected")
            logger.info("MockKasaDeviceClient: Simulating actual status query.")
            await asyncio.sleep(0.1)
            return self._mock_state


    # 暫時替換 KasaDeviceClient 為 Mock，以便在沒有實際 Kasa 設備時運行測試
    original_kasa_device_client = KasaDeviceClient
    KasaDeviceClient = MockKasaDeviceClient  # 在測試時使用 Mock


    async def test_kasa_plug_final_separated():
        plug = KasaSmartPlug(min_op_interval=3.0, update_interval=1.0)  # 不再傳遞 IP

        print("\n--- 測試：發送多個快速指令，觀察頻率限制 ---")
        await plug.turn_on()
        await asyncio.sleep(0.5)
        await plug.turn_off()
        await asyncio.sleep(0.5)
        await plug.turn_on()

        print("\n--- 等待背景任務執行並觀察狀態 ---")
        for i in range(10):
            status = await plug.is_on()
            intended = "ON" if plug._intended_state else ("OFF" if plug._intended_state is not None else "N/A")
            print(f"[{i + 1}s] Current physical state: {status} (Intended: {intended})")
            await asyncio.sleep(1)

        print("\n--- 測試：發送最終關閉指令 ---")
        await plug.turn_off()
        for i in range(5):
            status = await plug.is_on()
            intended = "ON" if plug._intended_state else ("OFF" if plug._intended_state is not None else "N/A")
            print(f"[{i + 1}s] Current physical state: {status} (Intended: {intended})")
            await asyncio.sleep(1)

        plug.cancel_updater_task()
        try:
            await plug._state_updater_task
        except asyncio.CancelledError:
            logger.info("Updater task confirmed cancelled.")
        except Exception as e:
            logger.error(f"Error while waiting for task cancellation: {e}")


    asyncio.run(test_kasa_plug_final_separated())

    # 恢復 KasaDeviceClient
    KasaDeviceClient = original_kasa_device_client

    print("\n--- KasaSmartPlug 結構測試完成 ---")