from dataclasses import dataclass, asdict


@dataclass
class DMAioModbusReadResponse:
    data: list[int]
    error: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DMAioModbusWriteResponse:
    status: bool
    error: str

    def to_dict(self) -> dict:
        return asdict(self)


class DMAioModbusInnerClient:
    async def read_coils(self, address: int, count: int = 1, slave: int = 1) -> DMAioModbusReadResponse:
        raise NotImplementedError

    async def read_discrete_inputs(self, address: int, count: int = 1, slave: int = 1) -> DMAioModbusReadResponse:
        raise NotImplementedError

    async def read_holding_registers(self, address: int, count: int = 1, slave: int = 1) -> DMAioModbusReadResponse:
        raise NotImplementedError

    async def read_input_registers(self, address: int, count: int = 1, slave: int = 1) -> DMAioModbusReadResponse:
        raise NotImplementedError

    async def write_coil(self, address: int, value: int, slave: int = 1) -> DMAioModbusWriteResponse:
        raise NotImplementedError

    async def write_register(self, address: int, value: int, slave: int = 1) -> DMAioModbusWriteResponse:
        raise NotImplementedError

    async def write_coils(self, address: int, values: list[int] | int, slave: int = 1) -> DMAioModbusWriteResponse:
        raise NotImplementedError

    async def write_registers(self, address: int, values: list[int] | int, slave: int = 1) -> DMAioModbusWriteResponse:
        raise NotImplementedError
