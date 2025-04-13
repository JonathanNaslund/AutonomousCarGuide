# serial_comms.py

import serial
import json
import time
from typing import Tuple, Optional

# Set up the serial port
uart = serial.Serial(
    port="/dev/serial0",   # Pi UART (TX/RX)
    baudrate=115200,
    timeout=0.1            # Non-blocking read
)

def send_status_to_esp32(position: Tuple[int, int], heading: float, car_id: str):
    message = {
        "id": car_id,
        "position": position,
        "heading": heading,
        "timestamp": time.time()
    }

    try:
        encoded = json.dumps(message) + "\n"
        uart.write(encoded.encode("utf-8"))
    except Exception as e:
        print(f"[UART] Failed to send: {e}")

def receive_message_from_esp32() -> Optional[dict]:
    try:
        line = uart.readline().decode("utf-8").strip()
        if line:
            return json.loads(line)
    except Exception as e:
        print(f"[UART] Failed to read/parse: {e}")
    return None
