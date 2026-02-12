#!/usr/bin/env python3
"""
Serial-based servo controller for Arduino Uno.

Drop-in replacement for servo_controller.py — communicates with the
Arduino over USB serial instead of driving GPIO PWM directly.

The Arduino runs servo_driver.ino and handles all PWM timing in
hardware, eliminating the jitter problem with RPi.GPIO software PWM.
"""

import serial
import time
import threading
import glob
import sys


def find_arduino_port() -> str:
    """Auto-detect the Arduino serial port."""
    if sys.platform.startswith("linux"):
        # Raspberry Pi / Linux — Arduino Uno shows up as ttyACM* or ttyUSB*
        candidates = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
    elif sys.platform == "win32":
        candidates = [f"COM{i}" for i in range(1, 20)]
    elif sys.platform == "darwin":
        candidates = glob.glob("/dev/tty.usbmodem*") + glob.glob("/dev/tty.usbserial*")
    else:
        candidates = []

    for port in sorted(candidates):
        try:
            s = serial.Serial(port, 9600, timeout=1)
            s.close()
            return port
        except (serial.SerialException, OSError):
            continue

    raise RuntimeError(
        "No Arduino found. Check USB cable and run: ls /dev/ttyACM* /dev/ttyUSB*"
    )


class SerialServoController:
    """Controls pan/tilt/trigger servos via Arduino over USB serial."""

    def __init__(self, port: str = "", baud: int = 9600):
        """
        Args:
            port: Serial port path (e.g. "/dev/ttyACM0").
                  Empty string = auto-detect.
            baud: Baud rate — must match the Arduino sketch (9600).
        """
        self.port = port or find_arduino_port()
        self.baud = baud
        self._conn = None
        self._lock = threading.Lock()

        # Angle limits
        self.pan_min = 0
        self.pan_max = 180
        self.tilt_min = 0
        self.tilt_max = 180

        # Center positions
        self.pan_center = 90
        self.tilt_center = 90

        # Current positions (tracked locally for fast reads)
        self.current_pan = self.pan_center
        self.current_tilt = self.tilt_center

        # Camera FOV (degrees) — adjust to match your webcam
        self.h_fov = 60.0
        self.v_fov = 45.0

        self._connect()

    # ------------------------------------------------------------------
    #  Serial helpers
    # ------------------------------------------------------------------

    def _connect(self):
        """Open serial connection and wait for Arduino boot."""
        self._conn = serial.Serial(self.port, self.baud, timeout=2)
        # Arduino Uno resets when serial opens — wait for bootloader
        time.sleep(2.0)
        # Read the "READY" message
        startup = self._read_line()
        print(f"Arduino on {self.port}: {startup}")

    def _send(self, command: str) -> str:
        """Send a command string and return the response line."""
        with self._lock:
            self._conn.write(f"{command}\n".encode("utf-8"))
            return self._read_line()

    def _read_line(self) -> str:
        """Read one line from serial (blocking up to timeout)."""
        try:
            return self._conn.readline().decode("utf-8").strip()
        except Exception:
            return ""

    # ------------------------------------------------------------------
    #  Movement — same interface as servo_controller.ServoController
    # ------------------------------------------------------------------

    def move_servo_smooth(self, target_pan: float, target_tilt: float):
        """Move pan and tilt servos to target angles.

        The Arduino Servo library moves instantly; smoothing is not
        needed because the mechanical inertia of SG90s already limits
        slew rate at the small steps we send (~20 Hz update rate).
        """
        target_pan = max(self.pan_min, min(self.pan_max, int(round(target_pan))))
        target_tilt = max(self.tilt_min, min(self.tilt_max, int(round(target_tilt))))

        self.current_pan = target_pan
        self.current_tilt = target_tilt

        # Single combined command — half the latency of two commands
        self._send(f"L{target_pan},{target_tilt}")

    def move_to_center(self):
        """Center all servos (pan, tilt, trigger)."""
        self.current_pan = self.pan_center
        self.current_tilt = self.tilt_center
        self._send("C")

    def track_target(self, frame_width: int, frame_height: int,
                     target_x: int, target_y: int):
        """Convert pixel coordinates to servo angles and move.

        Maps the target's offset from frame center to an angular offset
        based on the camera's field of view.
        """
        # Normalized offset: -1.0 (left/top) to +1.0 (right/bottom)
        offset_x = (frame_width / 2 - target_x) / (frame_width / 2)
        offset_y = (frame_height / 2 - target_y) / (frame_height / 2)

        pan_angle = self.pan_center + offset_x * (self.h_fov / 2)
        tilt_angle = self.tilt_center + offset_y * (self.v_fov / 2)

        self.move_servo_smooth(pan_angle, tilt_angle)

    # ------------------------------------------------------------------
    #  Trigger control
    # ------------------------------------------------------------------

    def set_trigger_position(self, angle: int):
        """Set the trigger servo to a specific angle."""
        self._send(f"G{int(angle)}")

    def fire(self):
        """Fire the trigger (Arduino handles hold timing)."""
        self._send("F")

    # ------------------------------------------------------------------
    #  Configuration
    # ------------------------------------------------------------------

    def set_limits(self, pan_min=None, pan_max=None,
                   tilt_min=None, tilt_max=None):
        if pan_min is not None:
            self.pan_min = pan_min
        if pan_max is not None:
            self.pan_max = pan_max
        if tilt_min is not None:
            self.tilt_min = tilt_min
        if tilt_max is not None:
            self.tilt_max = tilt_max

    def set_center_positions(self, pan_center=None, tilt_center=None):
        if pan_center is not None:
            self.pan_center = pan_center
        if tilt_center is not None:
            self.tilt_center = tilt_center

    def get_position(self) -> dict:
        """Request current positions from Arduino."""
        response = self._send("S")
        if response.startswith("POS:"):
            parts = response[4:].split(",")
            if len(parts) == 3:
                return {
                    "pan": int(parts[0]),
                    "tilt": int(parts[1]),
                    "trigger": int(parts[2]),
                }
        return {
            "pan": self.current_pan,
            "tilt": self.current_tilt,
            "trigger": 0,
        }

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    def cleanup(self):
        """Center servos and close serial connection."""
        try:
            self._send("C")
        except Exception:
            pass
        if self._conn and self._conn.is_open:
            self._conn.close()
        print("Serial servo controller cleaned up")

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
