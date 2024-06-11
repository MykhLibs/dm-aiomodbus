# DM-aiomodbus

## Urls

* [PyPI](https://pypi.org/project/dm-aiomodbus)
* [GitHub](https://github.com/DIMKA4621/dm-aiomodbus)

## Example

### Connection

* Serial
   ```python
   from dm_aiomodbus import DMAioModbusSerialClient

   modbus_client = DMAioModbusSerialClient(
       port="/dev/ttyUSB0",
       baudrate=9600,
       bytesize=8,
       stopbits=2,
       parity="N"
   )
   ```

* TCP
   ```python
   from dm_aiomodbus import DMAioModbusTcpClient

   modbus_client = DMAioModbusTcpClient(
       host="192.168.0.0",
       port=501
   )
   ```

* Simulator _(always returns mock data)_
   ```python
   from dm_aiomodbus import DMAioModbusSimulatorClient

   modbus_client = DMAioModbusSimulatorClient()
   ```

### Usage

```python
from dm_aiomodbus import DMAioModbusTcpClient
import asyncio


async def main():
    # create client
    modbus_client = DMAioModbusTcpClient(
        host="192.168.0.0",
        port=501,
        name_tag="my_tcp_plc"
    )

    # read registers
    # get values and error if any
    reg_258_259, err1 = await modbus_client.read_holding_registers(258, count=2)
    reg_256, err2 = await modbus_client.read_holding_registers(256)
    # read second slave-device
    reg_260_2, err3 = await modbus_client.read_holding_registers(address=260, slave=2)
    print(reg_258_259, reg_256, reg_260_2)

    # write registers
    # get write status and error if any
    status, err = await modbus_client.write_register(256, 1)
    # write second slave-device
    await modbus_client.write_register(260, value=0, slave=2)


if __name__ == "__main__":
    asyncio.run(main())
```

### Optional init parameters

| Parameter                  | Type  | Default Value | Description                                                         |
|----------------------------|-------|---------------|---------------------------------------------------------------------|
| `execute_timeout_s`        | `int` | `5`           | requests timeout (s)                                                |
| `disconnect_timeout_s`     | `int` | `20`          | timeout waiting for an active connection after the last request (s) |
| `after_execute_timeout_ms` | `int` | `3`           | timeout between requests (ms)                                       |

### Set custom logger

_If you want set up custom logger_

```python
from dm_aiomodbus import DMAioModbusTcpClient


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
