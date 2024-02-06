from __future__ import annotations
from typing import Callable, Coroutine, Type
from dm_logger import DMLogger
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus import ModbusException, ExceptionResponse
import asyncio
from .aiomodbus_temp_client import DMAioModbusTempClientInterface

__all__ = ['DMAioModbusBaseClient']


class DMAioModbusBaseClient:
    _TEMP_CALLBACK_TYPE = Callable[[DMAioModbusTempClientInterface], Coroutine]
    __logger = None

    def __init__(
        self,
        aio_modbus_lib_class: Type[AsyncModbusSerialClient | AsyncModbusTcpClient],
        modbus_config: dict[str, str | int],
        disconnect_timeout_s: float = 20,
        after_execute_timeout_ms: float = 3,
        name_tag: str = None
    ) -> None:
        if self.__logger is None:
            name_suffix = f"-{name_tag}" if name_tag is not None else ""
            self.__logger = DMLogger(f"{self.__class__.__name__}{name_suffix}")
        self.__logger.debug(**modbus_config)

        self.__actions = []
        self.__is_locked = False
        self.__disconnect_task = None
        self.__disconnect_time_s = disconnect_timeout_s if disconnect_timeout_s >= 0 else 1
        self.__after_execute_timeout_ms = after_execute_timeout_ms / 1000 if after_execute_timeout_ms >= 0 else 0.000
        self.__temp_client = self.__create_temp_client()
        self.__client = aio_modbus_lib_class(**modbus_config, timeout=1, retry=1)

    def execute(self, callback: _TEMP_CALLBACK_TYPE) -> None:
        async def _execute() -> None:
            self.__actions.append(callback)
            if self.__is_locked:
                return

            self.__is_locked = True
            if self.__disconnect_task is not None:
                self.__disconnect_task.cancel()

            if not self.__is_connected:
                await self.__connect()

            temp_cb = None
            while self.__actions or callable(temp_cb):
                if callable(temp_cb):
                    cb = temp_cb
                else:
                    cb = self.__actions.pop(0)
                    if not callable(cb):
                        cb_type = None if cb is None else type(cb)
                        self.__logger.error(f"Invalid callback: Expected callable, got {cb_type}")
                        continue

                try:
                    await cb(self.__temp_client)
                except Exception as e:
                    if not self.__is_connected:
                        self.__logger.error(f"Connection error: {e}.\nReconnecting...")
                        await self.__connect()
                    else:
                        self.__logger.error(e)
                    if callable(temp_cb):
                        temp_cb = None
                    else:
                        temp_cb = cb
                else:
                    temp_cb = None

            self.__is_locked = False
            self.__disconnect_task = asyncio.create_task(self.__wait_on_disconnect())

        _ = asyncio.create_task(_execute())

    async def execute_and_return(self, callback: _TEMP_CALLBACK_TYPE, timeout: float = 5):
        result_obj = {"result": None, "executed": False}

        async def return_from_callback(temp_client: DMAioModbusTempClientInterface):
            result_obj["result"] = await callback(temp_client)
            result_obj["executed"] = True

        self.execute(return_from_callback)

        wait_time = 1.5
        timeout = timeout if timeout > 0 else 1
        while not result_obj["executed"] and wait_time < timeout:
            await asyncio.sleep(0.01)
            wait_time += 0.01

        return result_obj["result"]

    @property
    def __is_connected(self) -> bool:
        return self.__client.connected

    async def __connect(self) -> None:
        try:
            if not await self.__client.connect():
                raise ConnectionError("No connection established")
            self.__logger.info("Connected!")
        except Exception as e:
            self.__logger.error(f"Connection error: {e}")

    async def __wait_on_disconnect(self) -> None:
        wait_time = 0
        while wait_time < self.__disconnect_time_s:
            await asyncio.sleep(0.1)
            wait_time += 0.1

        if self.__is_connected:
            self.__logger.info("Disconnected!")
            self.__client.close()

    async def __error_handler(self, method: Callable, kwargs: dict) -> None:
        kwargs = {**kwargs, "slave": 1}
        try:
            result = await method(**kwargs)
            await asyncio.sleep(self.__after_execute_timeout_ms)
            if result.isError() or isinstance(result, ExceptionResponse):
                raise ModbusException(f"Received error: {result}")
            return result
        except Exception as e:
            self.__logger.error(f"Error: {e}", method=method.__name__, params=kwargs)
            if not self.__is_connected:
                await self.__connect()

    async def __read(self, method, kwargs: dict) -> list | None:
        result = await self.__error_handler(method, kwargs)
        return result.registers if hasattr(result, "registers") else []

    async def __write(self, method, kwargs: dict) -> bool:
        result = await self.__error_handler(method, kwargs)
        return bool(result)

    async def __read_coils(self, address: int, count: int = 1) -> list | None:
        return await self.__read(self.__client.read_coils, {
            "address": address,
            "count": count
        })

    async def __read_discrete_inputs(self, address: int, count: int = 1) -> list | None:
        return await self.__read(self.__client.read_discrete_inputs, {
            "address": address,
            "count": count
        })

    async def __read_holding_registers(self, address: int, count: int = 1) -> list | None:
        return await self.__read(self.__client.read_holding_registers, {
            "address": address,
            "count": count
        })

    async def __read_input_registers(self, address: int, count: int = 1) -> list | None:
        return await self.__read(self.__client.read_input_registers, {
            "address": address,
            "count": count
        })

    async def __write_coil(self, address: int, value: int) -> bool:
        return await self.__write(self.__client.write_coil, {
            "address": address,
            "value": value,
        })

    async def __write_register(self, address: int, value: int) -> bool:
        return await self.__write(self.__client.write_register, {
            "address": address,
            "value": value,
        })

    async def __write_coils(self, address: int, values: list[int] | int) -> bool:
        return await self.__write(self.__client.write_coils, {
            "address": address,
            "values": values,
        })

    async def __write_registers(self, address: int, values: list[int] | int) -> bool:
        return await self.__write(self.__client.write_registers, {
            "address": address,
            "values": values,
        })

    def __create_temp_client(self) -> DMAioModbusTempClientInterface:
        allowed_methods = {
            "read_coils": self.__read_coils,
            "read_discrete_inputs": self.__read_discrete_inputs,
            "read_holding_registers": self.__read_holding_registers,
            "read_input_registers": self.__read_input_registers,
            "write_coil": self.__write_coil,
            "write_register": self.__write_register,
            "write_coils": self.__write_coils,
            "write_registers": self.__write_registers
        }

        class TempClient(DMAioModbusTempClientInterface):
            def __init__(self):
                for name, method in allowed_methods.items():
                    setattr(self, name, method)

        return TempClient()

    @classmethod
    def set_logger(cls, logger) -> None:
        if (hasattr(logger, "debug") and isinstance(logger.debug, Callable) and
            hasattr(logger, "info") and isinstance(logger.info, Callable) and
            hasattr(logger, "warning") and isinstance(logger.warning, Callable) and
            hasattr(logger, "error") and isinstance(logger.error, Callable)
        ):
            cls.__logger = logger
        else:
            print("Invalid logger")
