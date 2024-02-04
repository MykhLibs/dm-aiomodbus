from __future__ import annotations


class DMAioModbusTempClientInterface:
    def __init__(self, base_client):
        self.__base_client = base_client

    async def read_coils(self, address: int, count: int = 1) -> list | None:
        return await self.__base_client.read_coils(address, count)

    async def read_discrete_inputs(self, address: int, count: int = 1) -> list | None:
        return await self.__base_client.read_discrete_inputs(address, count)

    async def read_holding_registers(self, address: int, count: int = 1) -> list | None:
        return await self.__base_client.read_holding_registers(address, count)

    async def read_input_registers(self, address: int, count: int = 1) -> list | None:
        return await self.__base_client.read_input_registers(address, count)

    async def write_coil(self, address: int, value: int) -> bool:
        return await self.__base_client.write_coil(address, value)

    async def write_register(self, address: int, value: int) -> bool:
        return await self.__base_client.write_register(address, value)

    async def write_coils(self, address: int, values: list[int] | int) -> bool:
        return await self.__base_client.write_coils(address, values)

    async def write_registers(self, address: int, values: list[int] | int) -> bool:
        return await self.__base_client.write_registers(address, values)
