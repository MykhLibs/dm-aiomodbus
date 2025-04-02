from typing import Literal
from dataclasses import dataclass
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
    operation_timeout_ms: int = 100  # Not recommended set to less than 100
    error_logging: bool = False


class DMAioModbusSerialClient(DMAioModbusBaseClient):
    _logger_params = None

    def __init__(self, config: DMAioModbusSerialClientConfig) -> None:
        super().__init__(
            config=DMAioModbusBaseClientConfig(
                modbus_client=AsyncModbusSerialClient(
                    port=config.port,
                    baudrate=config.baudrate,
                    bytesize=config.bytesize,
                    stopbits=config.stopbits,
                    parity=config.parity,
                    timeout=1
                ),
                disconnect_timeout_s=config.disconnect_timeout_s,
                operation_timeout_ms=config.operation_timeout_ms,
                error_logging=config.error_logging
            )
        )

        if not isinstance(self._logger_params, dict):
            self._logger_params = {}
        if "name" not in self._logger_params:
            self._logger_params["name"] = f"{self.__class__.__name__}-{config.port}"
        self._set_logger()
