from typing import Literal
from dataclasses import dataclass
from dm_logger import DMLogger
from pymodbus.client import AsyncModbusSerialClient

from .aiomodbus_base_client import DMAioModbusBaseClient, DMAioModbusBaseClientConfig


@dataclass
class DMAioModbusSerialClientConfig:
    port: str
    baudrate: int = 9600
    bytesize: Literal[7, 8] = 8
    stopbits: Literal[1, 2] = 2
    parity: Literal["N", "E", "O"] = "N"
    disconnect_timeout_s: int = 20
    error_logging: bool = False


class DMAioModbusSerialClient(DMAioModbusBaseClient):
    def __init__(self, config: DMAioModbusSerialClientConfig) -> None:
        super().__init__(
            config=DMAioModbusBaseClientConfig(
                modbus_client=AsyncModbusSerialClient(
                    port=config.port,
                    baudrate=config.baudrate,
                    bytesize=config.bytesize,
                    stopbits=config.stopbits,
                    parity=config.parity
                ),
                disconnect_timeout_s=config.disconnect_timeout_s,
                error_logging=config.error_logging
            )
        )
        self._logger = DMLogger(f"{self.__class__.__name__}-{config.port}")
