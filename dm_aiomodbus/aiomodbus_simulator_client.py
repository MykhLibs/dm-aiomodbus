from __future__ import annotations
from typing import Callable
from pymodbus.client import AsyncModbusTcpClient
from .aiomodbus_base_client import DMAioModbusBaseClient


class DMAioModbusSimulatorClient(DMAioModbusBaseClient):
    def __init__(
        self,
        return_errors: bool = False,
        execute_timeout_s: int = None,
        disconnect_timeout_s: int = None,
        after_execute_timeout_ms: int = None,
        name_tag: str = None,
    ):
        super().__init__(
            aio_modbus_lib_class=AsyncModbusTcpClient,
            modbus_config={"host": "simulator"},
            return_errors=return_errors,
            execute_timeout_s=execute_timeout_s,
            disconnect_timeout_s=disconnect_timeout_s,
            after_execute_timeout_ms=after_execute_timeout_ms,
            name_tag=name_tag
        )
        self.__connected = False

    async def _read(self, method: Callable, kwargs: dict, group_name: str = None) -> list | (list, str):
        async def read_cb() -> (list, str):
            registers = [i for i in range(kwargs["count"])]
            if self._return_errors:
                return (registers, "")
            return registers

        return await self._execute_and_return(read_cb)

    async def _write(self, method: Callable, kwargs: dict, group_name: str = None) -> bool | (bool, str):
        async def write_cb() -> (bool, str):
            if self._return_errors:
                return (True, "")
            return True

        return await self._execute_and_return(write_cb)

    @property
    def _is_connected(self) -> bool:
        return self.__connected

    async def _connect(self) -> None:
        self.__connected = True

    def _disconnect(self) -> None:
        self.__connected = False
