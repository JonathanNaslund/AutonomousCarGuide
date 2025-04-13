# utils.py

import math
import time

def angle_difference(a: float, b: float) -> float:
    """Returns signed shortest angular distance from a to b."""
    return ((b - a + 180) % 360) - 180

def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min(val, max_val), min_val)

def wait_until(condition_fn, timeout=2.0, interval=0.05) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if condition_fn():
            return True
        time.sleep(interval)
    return False
