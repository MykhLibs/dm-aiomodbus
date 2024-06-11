from __future__ import annotations
from typing import Callable, Coroutine, Type
from dm_logger import DMLogger
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus import ModbusException, ExceptionResponse
from pymodbus.pdu import ModbusExceptions
import asyncio

__all__ = ['DMAioModbusBaseClient']


class DMAioModbusBaseClient:
    _CALLBACK_TYPE = Callable[[], Coroutine]
    _logger = None

    def __init__(
        self,
        aio_modbus_lib_class: Type[AsyncModbusSerialClient | AsyncModbusTcpClient],
        modbus_config: dict[str, str | int],
        return_errors: bool = False,
        execute_timeout_s: int = 5,
        disconnect_timeout_s: int = 20,
        after_execute_timeout_ms: int = 3,
        name_tag: str = None
    ) -> None:
        if self._logger is None:
            name_suffix = f"-{name_tag}" if name_tag is not None else ""
            self._logger = DMLogger(f"{self.__class__.__name__}{name_suffix}")
        self._logger.debug(**modbus_config)

        self.__actions = []
        self.__is_locked = False
        self.__current_group = False
        self.__disconnect_task = None
        self._return_errors = bool(return_errors)
        self.__execute_timeout_s, self.__disconnect_time_s, self.__after_execute_timeout_ms = self.__validate_timeouts(
            execute_timeout_s, disconnect_timeout_s, after_execute_timeout_ms
        )
        self.__client = aio_modbus_lib_class(**modbus_config, timeout=1, retry=1)

    async def read_coils(self, address: int, count: int = 1, slave: int = 1) -> list | (list, str):
        return await self._read(self.__client.read_coils, {
            "address": address,
            "count": count,
            "slave": slave
        })

    async def read_discrete_inputs(self, address: int, count: int = 1, slave: int = 1) -> list | (list, str):
        return await self._read(self.__client.read_discrete_inputs, {
            "address": address,
            "count": count,
            "slave": slave
        })

    async def read_holding_registers(self, address: int, count: int = 1, slave: int = 1) -> list | (list, str):
        return await self._read(self.__client.read_holding_registers, {
            "address": address,
            "count": count,
            "slave": slave
        })

    async def read_input_registers(self, address: int, count: int = 1, slave: int = 1) -> list | (list, str):
        return await self._read(self.__client.read_input_registers, {
            "address": address,
            "count": count,
            "slave": slave
        })

    async def write_coil(self, address: int, value: int, slave: int = 1) -> bool | (bool, str):
        return await self._write(self.__client.write_coil, {
            "address": address,
            "value": value,
            "slave": slave
        })

    async def write_register(self, address: int, value: int, slave: int = 1) -> bool | (bool, str):
        return await self._write(self.__client.write_register, {
            "address": address,
            "value": value,
            "slave": slave
        })

    async def write_coils(self, address: int, values: list[int] | int, slave: int = 1) -> bool | (bool, str):
        return await self._write(self.__client.write_coils, {
            "address": address,
            "values": values,
            "slave": slave
        })

    async def write_registers(self, address: int, values: list[int] | int, slave: int = 1) -> bool | (bool, str):
        return await self._write(self.__client.write_registers, {
            "address": address,
            "values": values,
            "slave": slave
        })

    async def _read(self, method: Callable, kwargs: dict) -> list | (list, str):
        async def read_cb() -> (list, str):
            result, error = await self.__error_handler(method, kwargs)
            if self._return_errors:
                return (result.registers, error) if hasattr(result, "registers") else ([], error)
            return result.registers if hasattr(result, "registers") else []

        return await self._execute_and_return(read_cb)

    async def _write(self, method: Callable, kwargs: dict) -> bool | (bool, str):
        async def write_cb() -> (bool, str):
            _, error = await self.__error_handler(method, kwargs)
            result = not error
            if self._return_errors:
                return (result, error)
            return result

        return await self._execute_and_return(write_cb)

    async def _execute_and_return(self, callback: _CALLBACK_TYPE) -> (list | bool, str):
        result_obj = {"result": None, "executed": False}

        async def return_from_callback() -> None:
            result_obj["result"] = await callback()
            result_obj["executed"] = True

        self.__execute(return_from_callback)

        wait_time = 1.5
        while not result_obj["executed"] and wait_time < self.__execute_timeout_s:
            await asyncio.sleep(0.01)
            wait_time += 0.01

        return result_obj["result"]

    async def __error_handler(self, method: Callable, kwargs: dict) -> (list | bool, str):
        result = None
        error = ""
        try:
            result = await method(**kwargs)
            await asyncio.sleep(self.__after_execute_timeout_ms)
            if result.isError() or isinstance(result, ExceptionResponse):
                error = f"{result.exception_code}_{ModbusExceptions.decode(result.exception_code)}"
                raise ModbusException(result)
        except Exception as e:
            self._logger.error(f"Error: {e}", method=method.__name__, params=kwargs)
            if not error:
                error = str(e)
            if not self._is_connected:
                await self._connect()
        return (result, error)

    def __execute(self, callback: _CALLBACK_TYPE) -> None:
        async def execute_cb() -> None:
            self.__actions.append(callback)
            if self.__is_locked:
                return

            self.__is_locked = True
            if self.__disconnect_task is not None:
                self.__disconnect_task.cancel()

            if not self._is_connected:
                await self._connect()

            temp_cb = None
            while self.__actions or callable(temp_cb):
                if callable(temp_cb):
                    cb = temp_cb
                else:
                    cb = self.__actions.pop(0)
                    if not callable(cb):
                        cb_type = None if cb is None else type(cb)
                        self._logger.error(f"Invalid callback: Expected callable, got {cb_type}")
                        continue
                try:
                    await cb()
                except Exception as e:
                    if not self._is_connected:
                        self._logger.error(f"Connection error: {e}.\nReconnecting...")
                        await self._connect()
                    else:
                        self._logger.error(e)
                    if callable(temp_cb):
                        temp_cb = None
                    else:
                        temp_cb = cb
                else:
                    temp_cb = None

            self.__is_locked = False
            self.__disconnect_task = asyncio.create_task(self.__wait_on_disconnect())

        _ = asyncio.create_task(execute_cb())

    @property
    def _is_connected(self) -> bool:
        return self.__client.connected

    async def _connect(self) -> None:
        try:
            if not await self.__client.connect():
                raise ConnectionError("No connection established")
        except Exception as e:
            self._logger.error(f"Connection error: {e}")

    def _disconnect(self) -> None:
        self.__client.close()

    async def __wait_on_disconnect(self) -> None:
        await asyncio.sleep(self.__disconnect_time_s)

        if self._is_connected:
            self._disconnect()

    def __validate_timeouts(
        self,
        execute_timeout_s: int,
        disconnect_timeout_s: int,
        after_execute_timeout_ms: int
    ) -> (int, int):
        if not isinstance(execute_timeout_s, int) or execute_timeout_s < 0:
            if execute_timeout_s is not None:
                self._logger.warning("Invalid execute_timeout_s value. Expected: value > 0. "
                                     "Is set to default value: 5")
            execute_timeout_s = 5
        if not isinstance(disconnect_timeout_s, int) or disconnect_timeout_s < 0:
            if disconnect_timeout_s is not None:
                self._logger.warning("Invalid disconnect_timeout_s value. Expected: value > 0. "
                                     "Is set to default value: 20")
            disconnect_timeout_s = 20
        if not isinstance(after_execute_timeout_ms, int) or after_execute_timeout_ms < 0:
            if after_execute_timeout_ms is not None:
                self._logger.warning("Invalid after_execute_timeout_ms value. Expected: value > 0. "
                                     "Is set to default value: 3")
            after_execute_timeout_ms = 3
        return execute_timeout_s, disconnect_timeout_s, after_execute_timeout_ms / 1000

    @classmethod
    def set_logger(cls, logger) -> None:
        if (hasattr(logger, "debug") and isinstance(logger.debug, Callable) and
            hasattr(logger, "info") and isinstance(logger.info, Callable) and
            hasattr(logger, "warning") and isinstance(logger.warning, Callable) and
            hasattr(logger, "error") and isinstance(logger.error, Callable)
        ):
            cls._logger = logger
        else:
            print("Invalid logger")
