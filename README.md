# DM-aiomodbus

### Asynchronous Modbus clients for Python with TCP and Serial connection support.

## Links

* [PyPI](https://pypi.org/project/dm-aiomodbus)
* [GitHub](https://github.com/MykhLibs/dm-aiomodbus)

---

| Section                                       | Description                                |
|-----------------------------------------------|--------------------------------------------|
| [Installation](#installation)                 | How to install the package                 |
| [Usage](#usage)                               | How to use the package                     |
| [Types](#types)                               | Types and classes used in the package      |
| [Inner Client Methods](#inner-client-methods) | List of methods available for inner client |

---

## Installation

Check if you have Python 3.12.6 or higher installed:

```bash
python3 --version
```

Install the package using pip:

```bash
pip install dm-aiomodbus
```

---

## Usage

### Windows Setup

```python
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

### Code Example

```python
import asyncio
from dm_aiomodbus import (
   DMAioModbusSerialClient, DMAioModbusSerialClientConfig,
   DMAioModbusTcpClient, DMAioModbusTcpClientConfig,
   DMAioModbusInnerClient
)


async def main():
    # Initialize Serial client
    serial_modbus_client = DMAioModbusSerialClient(
        config=DMAioModbusSerialClientConfig(
            port="/dev/ttyUSB0",
            baudrate=9600,  # default value
            bytesize=8,  # default value
            stopbits=2,  # default value
            parity="N",  # default value
            disconnect_timeout_s=20,  # default value
            error_logging=False  # default value
        )
    )

    # Initialize TCP client
    tcp_modbus_client = DMAioModbusTcpClient(
        config=DMAioModbusTcpClientConfig(
            host="129.168.1.5",
            port=502,  # default value
            disconnect_timeout_s=20,  # default value
            error_logging=False  # default value
        )
    )

    # Read/write register(s)
    async def callback(client: DMAioModbusInnerClient):
        await client.write_register(256, 1)
        result = await client.read_holding_registers(256, count=3)
        print(result)

    # Execute callback
    await serial_modbus_client.execute(callback)
    # or
    await tcp_modbus_client.execute(callback)


if __name__ == "__main__":
    asyncio.run(main())
```

**Note:** All read/write methods should be called inside your callback function

---

## Types

### Serial Client Config

```python
class DMAioModbusSerialClientConfig:
    port: str  # Serial port name. Example: "/dev/ttyS0" - Linux UART, "/dev/ttyUSB0" - linux USB, "COM1" - Windows USB
    baudrate: int = 9600  # Baudrate in bits per second
    bytesize: Literal[7, 8] = 8  # Number of data bits
    stopbits: Literal[1, 2] = 2  # Number of stop bits
    parity: Literal["N", "E", "O"] = "N"  # Parity mode. N - None, E - Even, O - Odd
    disconnect_timeout_s: int = 20  # Timeout in seconds
    error_logging: bool = False  # Enable error logging
```

### TCP Client Config

```python
class DMAioModbusTcpClientConfig:
    host: str  # IP address of the device
    port: int = 502  # Port number
    disconnect_timeout_s: int = 20  # Timeout in seconds
    error_logging: bool = False  # Enable error logging
```

### Read Response

```python
class DMAioModbusReadResponse:
    data: list[int]  # List of values read from device
    error: str  # Error message if operation failed
```

**Note:** This class has `to_dict()` method that returns a dictionary

**Warning:** If the operation failed, the `data` field will be an empty list

### Write Response

```python

class DMAioModbusWriteResponse:
    status: bool  # Boolean indicating success or failure
    error: str  # Error message if operation failed
```

**Note:** This class has `to_dict()` method that returns a dictionary

**Warning:** The status is considered True, if the operation did not result in an error.

---

## Inner Client Methods

| Method                   | Arguments                                                                | Response Type                    |
|--------------------------|--------------------------------------------------------------------------|----------------------------------|
| `read_coils`             | - *address* `int`<br>- *count* `int` = 1<br>- *slave* `int`= 1           | [ReadResponse](#read-response)   |
| `read_discrete_inputs`   | - *address* `int`<br>- *count* `int` = 1<br>- *slave* `int`= 1           | [ReadResponse](#read-response)   |
| `read_holding_registers` | - *address* `int`<br>- *count* `int` = 1<br>- *slave* `int`= 1           | [ReadResponse](#read-response)   |
| `read_input_registers`   | - *address* `int`<br>- *count* `int` = 1<br>- *slave* `int`= 1           | [ReadResponse](#read-response)   |
| `write_coil`             | - *address* `int`<br>- *value* `int`<br>- *slave* `int` = 1              | [WriteResponse](#write-response) |
| `write_register`         | - *address* `int`<br>- *value* `int`<br>- *slave* `int` = 1              | [WriteResponse](#write-response) |
| `write_coils`            | - *address* `int`<br>- *values* `list[int] \| int`<br>- *slave* `int`= 1 | [WriteResponse](#write-response) |
| `write_registers`        | - *address* `int`<br>- *values* `list[int] \| int`<br>- *slave* `int`= 1 | [WriteResponse](#write-response) |

### Parameters Description

- `address`: Register address _(single integer)_
- `count`: Number of items to read _(default: 1)_
- `value`/`values`: Value(s) to write _(single integer or list of integers)_
- `slave`: Slave unit address _(default: 1)_
