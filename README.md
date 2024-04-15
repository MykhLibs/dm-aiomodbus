# DM-aiomodbus

## Urls

* [PyPI](https://pypi.org/project/dm-aiomodbus)
* [GitHub](https://github.com/DIMKA4621/dm-aiomodbus)

## Usage

### Connection

* Serial
   ```python
   from dm_aiomodbus import DMAioModbusSerialClient

   modbus_client = DMAioModbusSerialClient(
       port="/dev/ttyUSB0",
       baudrate=9600,
       bytesize=8,
       stopbits=2,
       parity="N",
       name_tag="my_serial_plc"
   )
   ```

* TCP
   ```python
   from dm_aiomodbus import DMAioModbusTcpClient

   modbus_client = DMAioModbusTcpClient(
       host="192.168.0.0",
       port=501,
       name_tag="my_tcp_plc"
   )
   ```

### Requests
```python
from dm_aiomodbus import DMAioModbusTcpClient, DMAioModbusTempClientInterface
import asyncio


async def main():
    # create client
    modbus_client = DMAioModbusTcpClient(
        host="192.168.0.0",
        port=501,
        name_tag="my_tcp_plc"
    )

    # create read callback
    async def read_callback(client: DMAioModbusTempClientInterface):
        reg_258_259, err1 = await client.read_holding_registers(258, count=2)  # get values and error if any
        reg_256, err2 = await client.read_holding_registers(256)
        reg_260_2, err3 = await client.read_holding_registers(address=260, slave=2)  # read second slave-device
        print(reg_258_259, reg_256, reg_260_2)

    # create read callback
    async def write_callback(client: DMAioModbusTempClientInterface):
        status, err = await client.write_register(256, 1)  # get write status and error if any
        await client.write_register(260, value=0, slave=2)  # write second slave-device

    # request to plc
    modbus_client.execute(read_callback)  # execute without waiting result
    # or
    await modbus_client.execute_and_return(write_callback, timeout=3)  # execute and wait result with timeout 3s (default 5)


if __name__ == "__main__":
    asyncio.run(main())
```

### Optional init parameters

| Parameter                  | Type  | Default Value | Description                                                         |
|----------------------------|-------|---------------|---------------------------------------------------------------------|
| `disconnect_timeout_s`     | `int` | `20`          | timeout waiting for an active connection after the last request (s) |
| `after_execute_timeout_ms` | `int` | `3`           | timeout between requests (ms)                                       |

### Set custom logger

_If you want set up custom logger_

```python
from dm_aiomodbus import DMAioModbusTcpClient  # or another client


# create custom logger
class MyLogger:
    def debug(self, message):
        pass

    def info(self, message):
        pass

    def warning(self, message):
        print(message)

    def error(self, message):
        print(message)


# set up custom logger for all clients
DMAioModbusTcpClient.set_logger(MyLogger())
```

### Run in Windows

_If you run async code in **Windows**, set correct selector_

```python
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```
