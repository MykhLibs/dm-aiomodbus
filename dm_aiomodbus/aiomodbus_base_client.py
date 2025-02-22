import asyncio
import logging
from abc import ABC
from typing import Callable, Coroutine
from dataclasses import dataclass
from dm_logger import DMLogger
from pymodbus import ModbusException, ExceptionResponse
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.logging import pymodbus_apply_logging_config

from .types import DMAioModbusReadResponse, DMAioModbusWriteResponse, DMAioModbusInnerClient


@dataclass
class DMAioModbusBaseClientConfig:
    modbus_client: AsyncModbusSerialClient | AsyncModbusTcpClient
    disconnect_timeout_s: int = 20
    error_logging: bool = False


class DMAioModbusBaseClient(ABC):
    _OPERATION_TIMEOUT_MS: int = 100  # Not recommended set to less than 100
    _CALLBACK_TYPE = Callable[[DMAioModbusInnerClient], Coroutine[any, any, any]]

    def __init__(self, config: DMAioModbusBaseClientConfig):
        self._logger = DMLogger(self.__class__.__name__)
        pymodbus_apply_logging_config(logging.CRITICAL)  # Hide pymodbus warning logs

        self._modbus_client = config.modbus_client
        self._disconnect_time_s = config.disconnect_timeout_s or 20
        self._operation_timeout_s = self._OPERATION_TIMEOUT_MS / 1000
        self._error_logging = config.error_logging

        self._disconnect_task = None
        self._lock = asyncio.Lock()
        self._temp_client = self._create_temp_client()

    async def execute(self, callback: _CALLBACK_TYPE) -> any:
        async with self._lock:
            await self._check_connection()

            try:
                result = await callback(self._temp_client)
            except Exception as e:
                if self._error_logging:
                    self._logger.error(e)

            self._schedule_disconnect()
            return result

    async def _error_handler(self, method: Callable, kwargs: dict) -> (any, str):
        try:
            result = await method(**kwargs)
            if result.isError():
                error = f"{result.exception_code}_{self._get_exception_name(result)}"
                raise ModbusException(error)
            return result, ""
        except Exception as e:
            if self._error_logging:
                self._logger.error(e)
            return None, str(e)

    async def _read(self, method, kwargs: dict) -> DMAioModbusReadResponse:
        try:
            result, error = await asyncio.wait_for(
                self._error_handler(method, kwargs),
                timeout=self._operation_timeout_s
            )
            data = result.registers if hasattr(result, "registers") else []
            return DMAioModbusReadResponse(data, error)
        except asyncio.TimeoutError:
            return DMAioModbusReadResponse([], f"Operation timeout ({self._OPERATION_TIMEOUT_MS}ms)")

    async def _write(self, method: Callable, kwargs: dict) -> DMAioModbusWriteResponse:
        try:
            _, error = await asyncio.wait_for(
                self._error_handler(method, kwargs),
                timeout=self._operation_timeout_s
            )
            status = not bool(error)
            return DMAioModbusWriteResponse(status, error)
        except asyncio.TimeoutError:
            return DMAioModbusWriteResponse(False, f"Operation timeout ({self._OPERATION_TIMEOUT_MS}ms)")

    async def _read_coils(self, address: int, count: int = 1, slave: int = 1) -> DMAioModbusReadResponse:
        return await self._read(
            method=self._modbus_client.read_coils,
            kwargs={
                "address": address,
                "count": count,
                "slave": slave
            }
        )

    async def _read_discrete_inputs(self, address: int, count: int = 1, slave: int = 1) -> DMAioModbusReadResponse:
        return await self._read(
            method=self._modbus_client.read_discrete_inputs,
            kwargs={
                "address": address,
                "count": count,
                "slave": slave
            }
        )

    async def _read_holding_registers(self, address: int, count: int = 1, slave: int = 1) -> DMAioModbusReadResponse:
        return await self._read(
            method=self._modbus_client.read_holding_registers,
            kwargs={
                "address": address,
                "count": count,
                "slave": slave
            }
        )

    async def _read_input_registers(self, address: int, count: int = 1, slave: int = 1) -> DMAioModbusReadResponse:
        return await self._read(
            method=self._modbus_client.read_input_registers,
            kwargs={
                "address": address,
                "count": count,
                "slave": slave
            }
        )

    async def _write_coil(self, address: int, value: int, slave: int = 1) -> (bool, str):
        return await self._write(
            method=self._modbus_client.write_coil,
            kwargs={
                "address": address,
                "value": value,
                "slave": slave
            }
        )

    async def _write_register(self, address: int, value: int, slave: int = 1) -> (bool, str):
        return await self._write(
            method=self._modbus_client.write_register,
            kwargs={
                "address": address,
                "value": value,
                "slave": slave
            }
        )

    async def _write_coils(self, address: int, values: list[int] | int, slave: int = 1) -> (bool, str):
        return await self._write(
            method=self._modbus_client.write_coils,
            kwargs={
                "address": address,
                "values": values,
                "slave": slave
            }
        )

    async def _write_registers(self, address: int, values: list[int] | int, slave: int = 1) -> (bool, str):
        return await self._write(
            method=self._modbus_client.write_registers,
            kwargs={
                "address": address,
                "values": values,
                "slave": slave
            }
        )

    @property
    def _is_connected(self) -> bool:
        return self._modbus_client.connected

    async def _check_connection(self) -> None:
        if not self._is_connected:
            await self._modbus_client.connect()

    async def _wait_and_disconnect(self) -> None:
        await asyncio.sleep(self._disconnect_time_s)

        if self._is_connected:
            self._modbus_client.close()

    def _schedule_disconnect(self) -> None:
        if self._disconnect_task:
            self._disconnect_task.cancel()

        self._disconnect_task = asyncio.create_task(self._wait_and_disconnect())

    @staticmethod
    def _get_exception_name(response: ExceptionResponse) -> str:
        for attr, value in ExceptionResponse.__dict__.items():
            if isinstance(value, int) and value == response.exception_code:
                return attr
        return f"UNKNOWN_ERROR_{response.exception_code}"

    def _create_temp_client(self) -> DMAioModbusInnerClient:
        class InnerClient(DMAioModbusInnerClient):
            def __init__(self2):
                self2.read_coils = self._read_coils
                self2.read_discrete_inputs = self._read_discrete_inputs
                self2.read_holding_registers = self._read_holding_registers
                self2.read_input_registers = self._read_input_registers
                self2.write_coil = self._write_coil
                self2.write_register = self._write_register
                self2.write_coils = self._write_coils
                self2.write_registers = self._write_registers

        return InnerClient()
