#!/usr/bin/env python3
"""
Water gun controller that delegates servo operations to SerialServoController
(Arduino over USB serial) while managing all safety and targeting logic on the Pi.

Same public interface as water_gun_controller.WaterGunController so that
water_gun_server.py can use either backend interchangeably.
"""

import time
import threading
from serial_servo_controller import SerialServoController


class SerialWaterGunController:
    """Targeting + safety logic backed by an Arduino servo driver."""

    def __init__(self, port: str = "", baud: int = 9600):
        # Servo backend
        self.servo = SerialServoController(port, baud)

        # --- Safety state ---
        self.system_armed = False
        self.emergency_stop = False
        self.last_shot_time = 0.0
        self.shots_this_minute = 0
        self.minute_start_time = time.time()

        # --- Targeting state ---
        self.center_tolerance = 30        # pixels from center to consider "locked"
        self.lock_on_time = 2.0           # seconds target must stay centered
        self.lock_on_timer = 0.0
        self.target_locked = False

        # --- Timing limits ---
        self.trigger_cooldown = 3.0       # seconds between shots
        self.max_shots_per_minute = 10
        self.max_continuous_runtime = 300  # 5 minutes
        self.system_start_time = time.time()

    # ------------------------------------------------------------------
    #  Arm / Disarm
    # ------------------------------------------------------------------

    def arm_system(self):
        self.system_armed = True
        self.emergency_stop = False
        print("Water gun system ARMED")

    def disarm_system(self):
        self.system_armed = False
        self.servo.set_trigger_position(0)
        print("Water gun system DISARMED")

    def emergency_stop_trigger(self):
        self.emergency_stop = True
        self.system_armed = False
        self.servo.set_trigger_position(0)
        print("EMERGENCY STOP ACTIVATED")

    # ------------------------------------------------------------------
    #  Safety checks
    # ------------------------------------------------------------------

    def is_safe_to_fire(self) -> bool:
        now = time.time()

        # Reset per-minute counter
        if now - self.minute_start_time > 60:
            self.shots_this_minute = 0
            self.minute_start_time = now

        # Max runtime guard
        if now - self.system_start_time > self.max_continuous_runtime:
            print("Maximum runtime exceeded — system disarmed")
            self.disarm_system()
            return False

        return (
            self.system_armed
            and not self.emergency_stop
            and now - self.last_shot_time > self.trigger_cooldown
            and self.shots_this_minute < self.max_shots_per_minute
        )

    # ------------------------------------------------------------------
    #  Target lock
    # ------------------------------------------------------------------

    def check_target_lock(self, frame_width: int, frame_height: int,
                          target_x: int, target_y: int) -> bool:
        cx = frame_width // 2
        cy = frame_height // 2

        centered = (
            abs(target_x - cx) < self.center_tolerance
            and abs(target_y - cy) < self.center_tolerance
        )

        if centered:
            self.lock_on_timer += 0.1  # ~matches 10 Hz update rate
            if self.lock_on_timer >= self.lock_on_time:
                if not self.target_locked:
                    print("TARGET LOCKED")
                self.target_locked = True
            else:
                print(f"Locking on... {self.lock_on_timer:.1f}/{self.lock_on_time:.1f}s")
        else:
            self.lock_on_timer = 0.0
            if self.target_locked:
                print("Target lock lost")
            self.target_locked = False

        return self.target_locked

    # ------------------------------------------------------------------
    #  Firing
    # ------------------------------------------------------------------

    def fire_trigger(self) -> bool:
        if not self.is_safe_to_fire():
            return False
        if not self.target_locked:
            print("Cannot fire — target not locked")
            return False

        print("FIRING WATER GUN!")
        self.servo.fire()

        self.last_shot_time = time.time()
        self.shots_this_minute += 1
        print(f"Shot fired! ({self.shots_this_minute}/{self.max_shots_per_minute} this minute)")
        return True

    def manual_fire(self) -> bool:
        """Fire without requiring target lock (for testing)."""
        if self.is_safe_to_fire():
            self.target_locked = True  # bypass lock check
            threading.Thread(target=self.fire_trigger, daemon=True).start()
            return True
        print("Cannot fire — safety check failed")
        return False

    # ------------------------------------------------------------------
    #  Tracking
    # ------------------------------------------------------------------

    def track_target(self, frame_width: int, frame_height: int,
                     target_x: int, target_y: int):
        self.servo.track_target(frame_width, frame_height, target_x, target_y)

    def track_and_fire(self, frame_width: int, frame_height: int,
                       target_x: int, target_y: int):
        """Track the target and auto-fire when locked and safe."""
        self.track_target(frame_width, frame_height, target_x, target_y)

        if self.check_target_lock(frame_width, frame_height, target_x, target_y):
            if self.is_safe_to_fire():
                threading.Thread(target=self.fire_trigger, daemon=True).start()

    def move_to_center(self):
        self.servo.move_to_center()
        self.target_locked = False
        self.lock_on_timer = 0.0

    # ------------------------------------------------------------------
    #  Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        now = time.time()
        time_since_shot = (
            now - self.last_shot_time if self.last_shot_time > 0 else float("inf")
        )
        return {
            "armed": self.system_armed,
            "emergency_stop": self.emergency_stop,
            "target_locked": self.target_locked,
            "lock_on_progress": self.lock_on_timer / self.lock_on_time,
            "shots_this_minute": self.shots_this_minute,
            "time_since_last_shot": time_since_shot,
            "runtime": now - self.system_start_time,
            "can_fire": self.is_safe_to_fire(),
        }

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    def cleanup(self):
        self.disarm_system()
        self.servo.cleanup()
        print("Serial water gun controller cleanup complete")

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
