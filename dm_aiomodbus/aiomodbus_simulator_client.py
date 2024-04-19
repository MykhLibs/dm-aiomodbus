from __future__ import annotations
from pymodbus.client import AsyncModbusTcpClient
from .aiomodbus_base_client import DMAioModbusBaseClient


class DMAioModbusSimulatorClient(DMAioModbusBaseClient):
    def __init__(
        self,
        disconnect_timeout_s: int = None,
        after_execute_timeout_ms: int = None,
        name_tag: str = None,
    ):
        super().__init__(
            aio_modbus_lib_class=AsyncModbusTcpClient,
            modbus_config={"host": "simulator"},
            disconnect_timeout_s=disconnect_timeout_s,
            after_execute_timeout_ms=after_execute_timeout_ms,
            name_tag=name_tag
        )
        self.__connected = False

    @property
    def _is_connected(self) -> bool:
        return self.__connected

    async def _connect(self) -> None:
        self.__connected = True
        self._logger.info("Connected!")

    def _disconnect(self) -> None:
        self.__connected = False
        self._logger.info("Disconnected!")

    async def _read(self, method, kwargs: dict) -> (list, str):
        registers = [i for i in range(kwargs["count"])]
        return (registers, "")

    async def _write(self, method, kwargs: dict) -> (bool, str):
        return (True, "")
