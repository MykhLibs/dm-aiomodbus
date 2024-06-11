from __future__ import annotations
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from .aiomodbus_base_client import DMAioModbusBaseClient

__all__ = ["DMAioModbusSerialClient", "DMAioModbusTcpClient"]


class DMAioModbusSerialClient(DMAioModbusBaseClient):
    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        bytesize: int = 8,
        stopbits: int = 2,
        parity: str = "N",
        return_errors: bool = None,
        execute_timeout_s: int = None,
        disconnect_timeout_s: int = None,
        after_execute_timeout_ms: int = None,
        name_tag: str = None,
    ) -> None:
        modbus_config = {
            "port": port,
            "baudrate": baudrate,
            "bytesize": bytesize,
            "stopbits": stopbits,
            "parity": parity
        }
        name_tag = name_tag or port
        super().__init__(
            aio_modbus_lib_class=AsyncModbusSerialClient,
            modbus_config=modbus_config,
            return_errors=return_errors,
            execute_timeout_s=execute_timeout_s,
            disconnect_timeout_s=disconnect_timeout_s,
            after_execute_timeout_ms=after_execute_timeout_ms,
            name_tag=name_tag
        )


class DMAioModbusTcpClient(DMAioModbusBaseClient):
    def __init__(
        self,
        host: str,
        port: int,
        return_errors: bool = None,
        execute_timeout_s: int = None,
        disconnect_timeout_s: int = None,
        after_execute_timeout_ms: int = None,
        name_tag: str = None
    ) -> None:
        modbus_config = {
            "host": host,
            "port": port
        }
        name_tag = name_tag or f"{host}:{port}"
        super().__init__(
            aio_modbus_lib_class=AsyncModbusTcpClient,
            modbus_config=modbus_config,
            return_errors=return_errors,
            execute_timeout_s=execute_timeout_s,
            disconnect_timeout_s=disconnect_timeout_s,
            after_execute_timeout_ms=after_execute_timeout_ms,
            name_tag=name_tag
        )
