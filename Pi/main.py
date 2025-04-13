import time
from typing import Tuple, List, Dict, Any

from imu_handler import IMUHandler
from navigation import (
    calculate_angle_to,
    distance_between,
    angle_difference,
    current_position
)
from serial_comms import send_status_to_esp32, receive_message_from_esp32
from motor_control import set_throttle, set_steering_angle, stop_motors
from utils import clamp

# ========== CONFIGURATION ==========

WAYPOINTS = {
    "right": [...],  # replace with your real outer lane
    "left": [...]    # replace with your real inner/overtake lane
}

CAR_ID = "car_1"
LANE = "right"  # default starting lane
TICK_RATE = 30  # 30 updates per second
DELTA_T = 1.0 / TICK_RATE

# ========== CAR CLASS ==========

class Car:
    def __init__(
        self,
        car_id: str,
        waypoints: Dict[str, List[Tuple[int, int]]],
        lane: str,
        base_speed: float = 50,
        steer_gain: float = 0.8,
        arrival_threshold: float = 30,
        max_steering_angle: float = 30
    ):
        self.car_id = car_id
        self.index = 0
        self.lane = lane
        self.position = waypoints[lane][0]
        self.waypoints = waypoints
        self.known_cars: Dict[str, Dict[str, Any]] = {}

        self.base_speed = base_speed
        self.min_speed = 20
        self.steer_gain = steer_gain
        self.max_steering_angle = max_steering_angle
        self.arrival_threshold = arrival_threshold
        self.slow_radius = 100
        self.stop_radius = 40

    def get_active_waypoints(self) -> List[Tuple[int, int]]:
        return self.waypoints[self.lane]

    def handle_incoming_messages(self):
        msg = receive_message_from_esp32()
        if msg:
            if msg.get("id") != self.car_id:
                self.known_cars[msg["id"]] = msg
            if msg.get("command") == "start":
                self.running = True
            elif msg.get("command") == "stop":
                self.running = False

    def get_closest_index_in_lane(self, lane: str, current_heading: float) -> int:
        wps = self.waypoints[lane]
        min_dist = float("inf")
        closest_index = 0

        for i, wp in enumerate(wps):
            dist = distance_between(self.position, wp)
            desired_angle = calculate_angle_to(self.position, wp)
            error = angle_difference(current_heading, desired_angle)

            if abs(error) > 90:
                continue

            if dist < min_dist:
                min_dist = dist
                closest_index = i

        return closest_index

    def is_lane_clear_ahead(self, lane: str, lookahead: int = 3, safe_radius: float = 0.4) -> bool:
        wps = self.waypoints[lane]
        start_index = self.get_closest_index_in_lane(lane, 0)  # heading not needed here

        for offset in range(lookahead):
            idx = (start_index + offset) % len(wps)
            wp = wps[idx]
            for car_id, data in self.known_cars.items():
                if car_id == self.car_id or data.get("lane") != lane:
                    continue
                if distance_between(tuple(data["position"]), wp) < safe_radius:
                    return False
        return True

    def adjust_speed_based_on_traffic(self) -> float:
        my_pos = self.position
        my_lane = self.lane
        min_dist = float("inf")

        for car_id, data in self.known_cars.items():
            if car_id == self.car_id or data.get("lane") != my_lane:
                continue
            dist = distance_between(my_pos, tuple(data["position"]))
            if dist < min_dist:
                min_dist = dist

        if min_dist < self.stop_radius:
            return 0
        if min_dist < self.slow_radius:
            return max(self.min_speed, self.base_speed * (min_dist / self.slow_radius))
        return self.base_speed

    def decide_lane(self, current_heading: float):
        if self.lane == "right":
            if not self.is_lane_clear_ahead("right"):
                if self.is_lane_clear_ahead("left"):
                    self.index = self.get_closest_index_in_lane("left", current_heading)
                    self.lane = "left"
        else:
            if self.is_lane_clear_ahead("right"):
                self.index = self.get_closest_index_in_lane("right", current_heading)
                self.lane = "right"

    def smooth_drive_loop(self, imu: IMUHandler):
        while True:
            start_time = time.time()
            self.handle_incoming_messages()

            wps = self.get_active_waypoints()
            next_index = (self.index + 1) % len(wps)
            target_wp = wps[next_index]
            current_wp = wps[self.index]

            current_heading = imu.get_heading()
            self.decide_lane(current_heading)

            speed = self.adjust_speed_based_on_traffic()

            if distance_between(self.position, target_wp) < self.arrival_threshold:
                self.index = next_index
                continue

            desired_angle = calculate_angle_to(current_wp, target_wp)
            error = angle_difference(current_heading, desired_angle)

            steering = clamp(error * self.steer_gain, -self.max_steering_angle, self.max_steering_angle)
            set_steering_angle(steering)
            set_throttle(speed)

            send_status_to_esp32(self.position, current_heading, self.car_id)

            # Maintain consistent tick rate
            elapsed = time.time() - start_time
            self.position = current_position(self.position, current_heading, speed, elapsed)
            
            elapsed = time.time() - start_time
            sleep_time = max(0, DELTA_T - elapsed)
            time.sleep(sleep_time)

# ========== STARTUP ==========

if __name__ == "__main__":
    try:
        car = Car(CAR_ID, WAYPOINTS, LANE)
        imu = IMUHandler()
        car.smooth_drive_loop(imu)
    except KeyboardInterrupt:
        stop_motors()
        print(f"[{CAR_ID}] Stopped.")
