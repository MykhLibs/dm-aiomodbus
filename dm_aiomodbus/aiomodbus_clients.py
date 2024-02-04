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
        name_tag: str = None
    ) -> None:
        modbus_config = {
            "port": port,
            "baudrate": baudrate,
            "bytesize": bytesize,
            "stopbits": stopbits,
            "parity": parity
        }
        super().__init__(aio_modbus_lib_class=AsyncModbusSerialClient, modbus_config=modbus_config, name_tag=name_tag)

    @classmethod
    async def temp_connect(
        cls,
        callback: DMAioModbusBaseClient._TEMP_CALLBACK_TYPE,
        port: str,
        baudrate: int = 9600,
        bytesize: int = 8,
        stopbits: int = 2,
        parity: str = "N",
        name_tag: str = None
    ):
        modbus_config = {
            "port": port,
            "baudrate": baudrate,
            "bytesize": bytesize,
            "stopbits": stopbits,
            "parity": parity
        }
        return await super().temp_connect(
            callback,
            aio_modbus_lib_class=AsyncModbusSerialClient,
            modbus_config=modbus_config,
            name_tag=name_tag
        )


class DMAioModbusTcpClient(DMAioModbusBaseClient):
    def __init__(
        self,
        host: str,
        port: str,
        name_tag: str = None
    ) -> None:
        modbus_config = {
            "host": host,
            "port": port
        }
        super().__init__(aio_modbus_lib_class=AsyncModbusTcpClient, modbus_config=modbus_config, name_tag=name_tag)

    @classmethod
    async def temp_connect(
        cls,
        callback: DMAioModbusBaseClient._TEMP_CALLBACK_TYPE,
        host: str,
        port: str,
        name_tag: str = None
    ):
        modbus_config = {
            "host": host,
            "port": port
        }
        return await super().temp_connect(
            callback,
            aio_modbus_lib_class=AsyncModbusSerialClient,
            modbus_config=modbus_config,
            name_tag=name_tag
        )
