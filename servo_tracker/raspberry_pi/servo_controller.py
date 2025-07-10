import RPi.GPIO as GPIO
import time
import threading

class ServoController:
    def __init__(self, pan_pin=18, tilt_pin=19, frequency=50):
        """
        Initialize servo controller for pan-tilt system
        
        Args:
            pan_pin: GPIO pin for horizontal servo (default: 18)
            tilt_pin: GPIO pin for vertical servo (default: 19)
            frequency: PWM frequency in Hz (default: 50)
        """
        self.pan_pin = pan_pin
        self.tilt_pin = tilt_pin
        self.frequency = frequency
        
        # Servo angle limits (can be adjusted based on your servo specs)
        self.pan_min = 0
        self.pan_max = 180
        self.tilt_min = 0
        self.tilt_max = 180
        
        # Center positions
        self.pan_center = 90
        self.tilt_center = 90
        
        # Current positions
        self.current_pan = self.pan_center
        self.current_tilt = self.tilt_center
        
        # Movement smoothing parameters
        self.max_step = 5  # Maximum degrees per movement step
        self.step_delay = 0.02  # Delay between movement steps
        
        # Initialize GPIO
        self.setup_gpio()
        
        # Move to center position
        self.move_to_center()
        
    def setup_gpio(self):
        """Initialize GPIO pins and PWM"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pan_pin, GPIO.OUT)
        GPIO.setup(self.tilt_pin, GPIO.OUT)
        
        self.pan_pwm = GPIO.PWM(self.pan_pin, self.frequency)
        self.tilt_pwm = GPIO.PWM(self.tilt_pin, self.frequency)
        
        self.pan_pwm.start(0)
        self.tilt_pwm.start(0)
        
    def angle_to_duty_cycle(self, angle):
        """
        Convert angle (0-180) to duty cycle for servo control
        Standard servo: 1ms = 0°, 1.5ms = 90°, 2ms = 180°
        """
        # Clamp angle to valid range
        angle = max(0, min(180, angle))
        
        # Convert to duty cycle (2.5% to 12.5% for 0° to 180°)
        duty_cycle = 2.5 + (angle / 180.0) * 10.0
        return duty_cycle
        
    def set_servo_angle(self, servo_pwm, angle):
        """Set servo to specific angle"""
        duty_cycle = self.angle_to_duty_cycle(angle)
        servo_pwm.ChangeDutyCycle(duty_cycle)
        
    def move_servo_smooth(self, target_pan, target_tilt):
        """
        Move servos smoothly to target positions
        """
        # Clamp target angles to limits
        target_pan = max(self.pan_min, min(self.pan_max, target_pan))
        target_tilt = max(self.tilt_min, min(self.tilt_max, target_tilt))
        
        # Calculate movement steps
        pan_diff = target_pan - self.current_pan
        tilt_diff = target_tilt - self.current_tilt
        
        # Determine number of steps needed
        max_diff = max(abs(pan_diff), abs(tilt_diff))
        steps = max(1, int(max_diff / self.max_step))
        
        # Calculate step increments
        pan_step = pan_diff / steps
        tilt_step = tilt_diff / steps
        
        # Move in steps
        for i in range(steps):
            self.current_pan += pan_step
            self.current_tilt += tilt_step
            
            self.set_servo_angle(self.pan_pwm, self.current_pan)
            self.set_servo_angle(self.tilt_pwm, self.current_tilt)
            
            time.sleep(self.step_delay)
        
        # Ensure final position is exact
        self.current_pan = target_pan
        self.current_tilt = target_tilt
        self.set_servo_angle(self.pan_pwm, self.current_pan)
        self.set_servo_angle(self.tilt_pwm, self.current_tilt)
        
    def move_to_center(self):
        """Move both servos to center position"""
        self.move_servo_smooth(self.pan_center, self.tilt_center)
        
    def track_target(self, frame_width, frame_height, target_x, target_y):
        """
        Calculate servo angles to track a target at given coordinates
        
        Args:
            frame_width: Width of camera frame
            frame_height: Height of camera frame
            target_x: X coordinate of target center
            target_y: Y coordinate of target center
        """
        # Convert pixel coordinates to servo angles
        # Pan: left side of frame = higher angle, right side = lower angle
        pan_angle = self.pan_center + ((frame_width/2 - target_x) / frame_width) * 90
        
        # Tilt: top of frame = higher angle, bottom = lower angle
        tilt_angle = self.tilt_center + ((frame_height/2 - target_y) / frame_height) * 90
        
        # Move servos to calculated positions
        self.move_servo_smooth(pan_angle, tilt_angle)
        
    def set_limits(self, pan_min=None, pan_max=None, tilt_min=None, tilt_max=None):
        """Set servo movement limits"""
        if pan_min is not None:
            self.pan_min = pan_min
        if pan_max is not None:
            self.pan_max = pan_max
        if tilt_min is not None:
            self.tilt_min = tilt_min
        if tilt_max is not None:
            self.tilt_max = tilt_max
            
    def set_center_positions(self, pan_center=None, tilt_center=None):
        """Set center positions for servos"""
        if pan_center is not None:
            self.pan_center = pan_center
        if tilt_center is not None:
            self.tilt_center = tilt_center
            
    def cleanup(self):
        """Clean up GPIO resources"""
        self.pan_pwm.stop()
        self.tilt_pwm.stop()
        GPIO.cleanup()
        
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass
