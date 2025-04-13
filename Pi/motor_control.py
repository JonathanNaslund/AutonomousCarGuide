# motor_control.py (Updated for PCA9685 and ESC + Steering Servo)

from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio

# Create the I2C bus interface
i2c = busio.I2C(SCL, SDA)

# Create a PCA9685 instance
pca = PCA9685(i2c)
pca.frequency = 50  # Standard for servo/ESC control (50Hz)

# === CONFIGURATION ===
THROTTLE_CHANNEL = 0  # PWM channel for ESC (driving motor)
STEERING_CHANNEL = 1  # PWM channel for steering servo

# These values depend on calibration of your ESC and servo
MIN_PULSE = 1000  # microseconds
MAX_PULSE = 2000  # microseconds

# Convert microseconds to 16-bit duty cycle (0-65535)
def pulse_width_to_duty(pulse_us):
    # Convert microseconds to duty cycle (assuming 50Hz = 20,000us per cycle)
    return int((pulse_us / 20000) * 65535)

# === Throttle Control ===
def set_throttle(power_percent: float):
    """
    Sets the ESC throttle. ESC expects 1-2ms PWM pulse:
    - 1.5ms is neutral (0%)
    - <1.5ms is reverse
    - >1.5ms is forward
    """
    pulse = 1500 + (power_percent * 5)  # Map -100 to +100 to 1000-2000us
    pulse = max(MIN_PULSE, min(MAX_PULSE, pulse))
    duty = pulse_width_to_duty(pulse)
    pca.channels[THROTTLE_CHANNEL].duty_cycle = duty

# === Steering Control ===
def set_steering_angle(angle: float):
    """
    Set steering angle.
    - angle = 0 is center
    - Negative = left, Positive = right
    """
    pulse = 1500 + (angle * 5)  # Map ~-30 to +30 degrees to PWM
    pulse = max(MIN_PULSE, min(MAX_PULSE, pulse))
    duty = pulse_width_to_duty(pulse)
    pca.channels[STEERING_CHANNEL].duty_cycle = duty

# === Stop the Car ===
def stop_motors():
    set_throttle(0)
    set_steering_angle(0)
