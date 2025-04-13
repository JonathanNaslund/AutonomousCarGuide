# master.py

import serial
import json
import time

# === CONFIG ===
PORT = "/dev/serial0"      # Or use '/dev/ttyUSB0' if using USB-to-serial
BAUDRATE = 115200

# Initialize UART connection to ESP32
uart = serial.Serial(
    port=PORT,
    baudrate=BAUDRATE,
    timeout=1
)

def send_command(command: str):
    msg = {
        "command": command,
        "timestamp": time.time()
    }
    try:
        encoded = json.dumps(msg) + "\n"
        uart.write(encoded.encode("utf-8"))
        print(f"[MASTER] Sent: {encoded.strip()}")
    except Exception as e:
        print(f"[MASTER] Failed to send command: {e}")

def main():
    while True:
        user_input = input(">> ").strip().lower()
        if user_input in ["start", "stop"]:
            send_command(user_input)
        elif user_input == "exit":
            print("Exiting master control.")
            break
        else:
            print("Unknown command. Use: start, stop, or exit.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[MASTER] Shutdown.")
