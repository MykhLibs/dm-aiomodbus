from dataclasses import dataclass
from dm_logger import DMLogger
from pymodbus.client import AsyncModbusTcpClient

from .aiomodbus_base_client import DMAioModbusBaseClient, DMAioModbusBaseClientConfig


@dataclass
class DMAioModbusTcpClientConfig:
    host: str
    port: int = 502
    disconnect_timeout_s: int = 20
    operation_timeout_ms: int = 100  # For remote TCP connections, it is recommended to set 200 or higher.
    error_logging: bool = False


class DMAioModbusTcpClient(DMAioModbusBaseClient):
    def __init__(self, config: DMAioModbusTcpClientConfig):
        super().__init__(
            config=DMAioModbusBaseClientConfig(
                modbus_client=AsyncModbusTcpClient(
                    host=config.host,
                    port=config.port,
                    timeout=1
                ),
                disconnect_timeout_s=config.disconnect_timeout_s,
                operation_timeout_ms=config.operation_timeout_ms,
                error_logging=config.error_logging
            )
        )
        self._logger = DMLogger(f"{self.__class__.__name__}-{config.host}:{config.port}")
