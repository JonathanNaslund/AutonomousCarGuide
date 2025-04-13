# imu_handler.py

import time
from board import SCL, SDA
import busio
import adafruit_bno08x
from adafruit_bno08x.i2c import BNO08X_I2C
import math

class IMUHandler:
    def __init__(self):
        i2c = busio.I2C(SCL, SDA)
        self.bno = BNO08X_I2C(i2c)
        self.bno.enable_feature(adafruit_bno08x.BNO_REPORT_ROTATION_VECTOR)

    def get_heading(self) -> float:
        quat = self.bno.quaternion  # (i, j, k, real)
        i, j, k, real = quat
        ysqr = j * j
        t3 = 2.0 * (real * k + i * j)
        t4 = 1.0 - 2.0 * (ysqr + k * k)
        yaw = math.atan2(t3, t4)
        return (math.degrees(yaw) + 360) % 360


