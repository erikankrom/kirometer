"""Read USB serial metadata without opening or resetting any device."""
import json
from serial.tools import list_ports

if __name__ == '__main__':
    print(json.dumps([
        {key: getattr(port, key, None) for key in
         ('device', 'description', 'serial_number', 'manufacturer', 'vid', 'pid')}
        for port in list_ports.comports() if port.vid is not None
    ]))
