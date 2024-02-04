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
    _LOG_FN_TYPE = Callable[[str], None]

    __reconnect_interval: int = 5
    __logger = None

    def __init__(
        self,
        aio_modbus_lib_class: Type[AsyncModbusSerialClient | AsyncModbusTcpClient],
        modbus_config: dict[str, str | int],
        name_tag: str = None
    ) -> None:
        if self.__logger is None:
            name_suffix = f"-{name_tag}" if name_tag is not None else ""
            self.__logger = DMLogger(f"{self.__class__.__name__}{name_suffix}")

        self.__modbus_config = {**modbus_config, "timeout": 1, "retry": 1}
        self.__aio_modbus_lib_class = aio_modbus_lib_class
        self.__client: AsyncModbusSerialClient | AsyncModbusTcpClient = None
        self.__soft_discon = False

    @property
    def is_exists(self) -> bool:
        return self.__client is not None

    @property
    def is_connected(self) -> bool:
        return self.is_exists and self.__client.connected

    async def __connect(self) -> None:
        self.__client = self.__aio_modbus_lib_class(**self.__modbus_config)
        if not await self.__client.connect():
            raise ConnectionError("No connection established")
        self.__logger.info("Connected!")

    async def connect(self) -> None:
        if self.is_connected:
            self.__logger.error("Client is already connected!")
            return

        async def _reconnect_loop(exit_after_connect: bool = False) -> None:
            while True:
                try:
                    if not self.is_connected:
                        await self.__connect()
                    if exit_after_connect:
                        break
                    while True:
                        if not self.is_exists:
                            return
                        if self.__client.connected:
                            await asyncio.sleep(0.1)
                        else:
                            raise ConnectionError("The connection is lost")
                except Exception as e:
                    self.__client.close()
                    self.__logger.error(
                        f"Connection error: {e}.\nReconnecting in {self.__reconnect_interval} seconds...")
                    await asyncio.sleep(self.__reconnect_interval)

        await _reconnect_loop(exit_after_connect=True)
        _ = asyncio.create_task(_reconnect_loop())
        await asyncio.sleep(0.001)

    def __soft_disconnect(self):
        if self.is_exists:
            if not self.__soft_discon:
                self.__soft_discon = True
                self.__logger.info("Disconnected!")
            self.__client.close()

    def disconnect(self) -> None:
        if self.is_exists:
            if self.is_connected:
                self.__logger.info("Disconnected!")
            else:
                self.__logger.warning("Client is not connected!")
            self.__client.close()
            self.__client = None

    @classmethod
    async def temp_connect(
        cls,
        callback: _TEMP_CALLBACK_TYPE,
        aio_modbus_lib_class: Type[AsyncModbusSerialClient | AsyncModbusTcpClient],
        modbus_config: dict[str, str | int],
        name_tag: str = None,
    ):
        if not callable(callback):
            cls.__logger.error(f"Callback is not a Callable object: {type(callback)}")
            return

        if cls.__logger is None:
            name_suffix = f"-{name_tag}" if name_tag is not None else ""
            logger = DMLogger(f"{cls.__name__}{name_suffix}")
        else:
            logger = cls.__logger

        client = DMAioModbusBaseClient(aio_modbus_lib_class, modbus_config, name_tag)

        try:
            temp_client = DMAioModbusTempClientInterface(client)
            await client.connect()
            try:
                return await callback(temp_client)
            except Exception as e:
                logger.error(f"Callback error: {e}")
            finally:
                cls.__soft_disconnect(client)
                cls.__soft_discon = False
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except Exception as e:
            logger.error(f"Error: {e}")

    async def __execute(self, method_name: str, kwargs: dict) -> None:
        skip = False
        if self.is_exists and not self.is_connected:
            self.__logger.warning("Action on pause! Waiting for reconnection...", action=method_name, params=kwargs)
            retries = 0
            while not self.is_connected:
                if retries >= self.__reconnect_interval + 1:
                    skip = True
                    break
                await asyncio.sleep(0.1)
                retries += 0.1
        if not self.is_exists or skip:
            self.__logger.warning("Action skipped! Client is not connected!", action=method_name, params=kwargs)

        if hasattr(self.__client, method_name):
            async_method = getattr(self.__client, method_name)
            if callable(async_method):
                try:
                    result = await async_method(**kwargs)
                    if result.isError() or isinstance(result, ExceptionResponse):
                        raise ModbusException(f"Received error: {result}")
                    return result
                except ModbusException as e:
                    self.__logger.error(e, action=method_name, params=kwargs)
                    self.__soft_disconnect()
                except Exception as e:
                    self.__logger.error(f"Error: {e}", action=method_name, params=kwargs)
                    self.__soft_disconnect()
            else:
                self.__logger.error(f"Attribute '{method_name}' found, but it's not a method", method=method_name)
        else:
            self.__logger.error(f"Method '{method_name}' not found", method=method_name)

    async def __read_register(self, method_name: str, address: int, count: int) -> list | None:
        kwargs = {
            "address": address,
            "count": count,
            "slave": 1
        }
        result = await self.__execute(method_name, kwargs)
        if result is None:
            return None

        result_data = result.registers if hasattr(result, "registers") else []
        if count != len(result_data):
            self.__logger.warning(f"Expected {count} registers, got {len(result_data)}",
                                  action=method_name, address=address, count=count)
        return result_data

    async def __write(self, method_name: str, address: int, value_obj: dict) -> bool:
        kwargs = {
            "address": address,
            **value_obj,
            "slave": 1,
        }
        result = await self.__execute(method_name, kwargs)
        return bool(result)

    async def read_coils(self, address: int, count: int = 1) -> list | None:
        return await self.__read_register("read_coils", address, count)

    async def read_discrete_inputs(self, address: int, count: int = 1) -> list | None:
        return await self.__read_register("read_discrete_inputs", address, count)

    async def read_holding_registers(self, address: int, count: int = 1) -> list | None:
        return await self.__read_register("read_holding_registers", address, count)

    async def read_input_registers(self, address: int, count: int = 1) -> list | None:
        return await self.__read_register("read_input_registers", address, count)

    async def write_coil(self, address: int, value: int) -> bool:
        return await self.__write("write_coil", address, {"value": value})

    async def write_register(self, address: int, value: int) -> bool:
        return await self.__write("write_register", address, {"value": value})

    async def write_coils(self, address: int, values: list[int] | int) -> bool:
        return await self.__write("write_coils", address, {"values": values})

    async def write_registers(self, address: int, values: list[int] | int) -> bool:
        return await self.__write("write_registers", address, {"values": values})

    @classmethod
    def get_reconnect_interval(cls) -> int:
        return cls.__reconnect_interval

    @classmethod
    def set_reconnect_interval(cls, interval: int) -> None:
        if not isinstance(interval, int):
            print(f"Invalid interval type: expected 'int', got {type(interval)}")
            return
        if interval < 1:
            print(f"Reconnect interval must be > 1")
            return
        cls.__reconnect_interval = interval

    @classmethod
    def set_logger(cls, logger) -> None:
        if (hasattr(logger, "info") and isinstance(logger.info, Callable) and
            hasattr(logger, "warning") and isinstance(logger.warning, Callable) and
            hasattr(logger, "error") and isinstance(logger.error, Callable)
        ):
            cls.__logger = logger
        else:
            print("Invalid logger")
