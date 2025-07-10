#!/usr/bin/env python3
"""
Enhanced Servo Controller with Water Gun Trigger Control
Extends the basic servo controller to include trigger firing capability
"""

import RPi.GPIO as GPIO
import time
import threading
from servo_controller import ServoController

class WaterGunController(ServoController):
    """Extended servo controller with trigger control for water gun alarm"""
    
    def __init__(self, pan_pin=18, tilt_pin=19, trigger_pin=20, frequency=50):
        """
        Initialize water gun controller
        
        Args:
            pan_pin: GPIO pin for horizontal servo
            tilt_pin: GPIO pin for vertical servo  
            trigger_pin: GPIO pin for trigger servo
            frequency: PWM frequency in Hz
        """
        # Initialize base servo controller
        super().__init__(pan_pin, tilt_pin, frequency)
        
        # Trigger servo setup
        self.trigger_pin = trigger_pin
        self.trigger_pwm = None
        
        # Trigger positions (adjust these for your water gun)
        self.trigger_rest_angle = 0      # Trigger not pulled
        self.trigger_fire_angle = 90     # Trigger fully pulled
        
        # Safety and timing parameters
        self.system_armed = False
        self.emergency_stop = False
        self.last_shot_time = 0
        self.shots_this_minute = 0
        self.minute_start_time = time.time()
        
        # Targeting parameters
        self.center_tolerance = 30       # pixels from center to fire
        self.lock_on_time = 2.0         # seconds target must be centered
        self.lock_on_timer = 0
        self.target_locked = False
        
        # Timing parameters
        self.trigger_pull_duration = 0.5  # seconds to hold trigger
        self.trigger_cooldown = 3.0       # seconds between shots
        self.max_shots_per_minute = 10
        self.max_continuous_runtime = 300  # 5 minutes
        self.system_start_time = time.time()
        
        # Initialize trigger servo
        self.setup_trigger_servo()
        
    def setup_trigger_servo(self):
        """Initialize trigger servo GPIO and PWM"""
        if not hasattr(self, 'trigger_pin'):
            return
            
        try:
            GPIO.setup(self.trigger_pin, GPIO.OUT)
            self.trigger_pwm = GPIO.PWM(self.trigger_pin, self.frequency)
            self.trigger_pwm.start(0)
            
            # Set trigger to rest position
            self.set_trigger_position(self.trigger_rest_angle)
            print(f"Trigger servo initialized on GPIO{self.trigger_pin}")
            
        except Exception as e:
            print(f"Failed to initialize trigger servo: {e}")
            self.trigger_pwm = None
            
    def set_trigger_position(self, angle):
        """Set trigger servo to specific angle"""
        if self.trigger_pwm:
            duty_cycle = self.angle_to_duty_cycle(angle)
            self.trigger_pwm.ChangeDutyCycle(duty_cycle)
            
    def arm_system(self):
        """Arm the water gun system"""
        self.system_armed = True
        self.emergency_stop = False
        print("🔫 Water gun system ARMED")
        
    def disarm_system(self):
        """Disarm the water gun system"""
        self.system_armed = False
        self.set_trigger_position(self.trigger_rest_angle)
        print("🛡️ Water gun system DISARMED")
        
    def emergency_stop_trigger(self):
        """Emergency stop - immediately disarm"""
        self.emergency_stop = True
        self.system_armed = False
        self.set_trigger_position(self.trigger_rest_angle)
        print("🚨 EMERGENCY STOP ACTIVATED")
        
    def is_safe_to_fire(self):
        """Check if it's safe to fire the water gun"""
        current_time = time.time()
        
        # Reset shots counter every minute
        if current_time - self.minute_start_time > 60:
            self.shots_this_minute = 0
            self.minute_start_time = current_time
            
        # Check runtime limit
        if current_time - self.system_start_time > self.max_continuous_runtime:
            print("⏰ Maximum runtime exceeded - system disarmed")
            self.disarm_system()
            return False
            
        return (
            self.system_armed and
            not self.emergency_stop and
            current_time - self.last_shot_time > self.trigger_cooldown and
            self.shots_this_minute < self.max_shots_per_minute
        )
        
    def check_target_lock(self, frame_width, frame_height, target_x, target_y):
        """Check if target is centered and locked on"""
        frame_center_x = frame_width // 2
        frame_center_y = frame_height // 2
        
        # Check if target is within center tolerance
        target_centered = (
            abs(target_x - frame_center_x) < self.center_tolerance and
            abs(target_y - frame_center_y) < self.center_tolerance
        )
        
        current_time = time.time()
        
        if target_centered:
            self.lock_on_timer += 0.1  # Assume this is called every 100ms
            if self.lock_on_timer >= self.lock_on_time:
                if not self.target_locked:
                    print("🎯 TARGET LOCKED")
                self.target_locked = True
            else:
                print(f"🔍 Locking on... {self.lock_on_timer:.1f}/{self.lock_on_time:.1f}s")
        else:
            self.lock_on_timer = 0
            if self.target_locked:
                print("❌ Target lock lost")
            self.target_locked = False
            
        return self.target_locked
        
    def fire_trigger(self):
        """Fire the water gun trigger"""
        if not self.is_safe_to_fire():
            return False
            
        if not self.target_locked:
            print("⚠️ Cannot fire - target not locked")
            return False
            
        print("💥 FIRING WATER GUN!")
        
        # Pull trigger
        self.set_trigger_position(self.trigger_fire_angle)
        
        # Hold for specified duration
        time.sleep(self.trigger_pull_duration)
        
        # Release trigger
        self.set_trigger_position(self.trigger_rest_angle)
        
        # Update shot tracking
        self.last_shot_time = time.time()
        self.shots_this_minute += 1
        
        print(f"💧 Shot fired! ({self.shots_this_minute}/{self.max_shots_per_minute} this minute)")
        return True
        
    def track_and_fire(self, frame_width, frame_height, target_x, target_y):
        """Track target and fire if conditions are met"""
        # Update servo positions for tracking
        self.track_target(frame_width, frame_height, target_x, target_y)
        
        # Check for target lock
        if self.check_target_lock(frame_width, frame_height, target_x, target_y):
            # Fire if locked and safe
            if self.is_safe_to_fire():
                threading.Thread(target=self.fire_trigger, daemon=True).start()
                
    def manual_fire(self):
        """Manually fire the water gun (for testing)"""
        if self.is_safe_to_fire():
            threading.Thread(target=self.fire_trigger, daemon=True).start()
            return True
        else:
            print("⚠️ Cannot fire - safety check failed")
            return False
            
    def test_trigger(self):
        """Test trigger mechanism without safety checks"""
        print("🧪 Testing trigger mechanism...")
        
        # Pull trigger slowly
        for angle in range(self.trigger_rest_angle, self.trigger_fire_angle + 1, 5):
            self.set_trigger_position(angle)
            time.sleep(0.1)
            
        time.sleep(0.5)
        
        # Release trigger slowly
        for angle in range(self.trigger_fire_angle, self.trigger_rest_angle - 1, -5):
            self.set_trigger_position(angle)
            time.sleep(0.1)
            
        print("✅ Trigger test complete")
        
    def calibrate_trigger(self):
        """Interactive trigger calibration"""
        print("\n🔧 Trigger Calibration Mode")
        print("Commands:")
        print("  +: Increase trigger angle")
        print("  -: Decrease trigger angle")
        print("  f: Fire (test current angle)")
        print("  r: Reset to rest position")
        print("  s: Save current angle as fire position")
        print("  q: Quit calibration")
        
        current_angle = self.trigger_rest_angle
        self.set_trigger_position(current_angle)
        
        while True:
            print(f"\nCurrent trigger angle: {current_angle}°")
            command = input("Enter command: ").lower().strip()
            
            if command == 'q':
                break
            elif command == '+':
                current_angle = min(180, current_angle + 5)
                self.set_trigger_position(current_angle)
            elif command == '-':
                current_angle = max(0, current_angle - 5)
                self.set_trigger_position(current_angle)
            elif command == 'f':
                print("Testing fire...")
                self.set_trigger_position(current_angle)
                time.sleep(0.5)
                self.set_trigger_position(self.trigger_rest_angle)
            elif command == 'r':
                current_angle = self.trigger_rest_angle
                self.set_trigger_position(current_angle)
            elif command == 's':
                self.trigger_fire_angle = current_angle
                print(f"Fire angle saved: {current_angle}°")
            else:
                print("Unknown command")
                
        # Return to rest position
        self.set_trigger_position(self.trigger_rest_angle)
        print("Calibration complete")
        
    def get_status(self):
        """Get system status"""
        current_time = time.time()
        runtime = current_time - self.system_start_time
        time_since_shot = current_time - self.last_shot_time if self.last_shot_time > 0 else float('inf')
        
        return {
            'armed': self.system_armed,
            'emergency_stop': self.emergency_stop,
            'target_locked': self.target_locked,
            'lock_on_progress': self.lock_on_timer / self.lock_on_time,
            'shots_this_minute': self.shots_this_minute,
            'time_since_last_shot': time_since_shot,
            'runtime': runtime,
            'can_fire': self.is_safe_to_fire()
        }
        
    def cleanup(self):
        """Clean up GPIO resources including trigger servo"""
        # Disarm system first
        self.disarm_system()
        
        # Clean up trigger servo
        if self.trigger_pwm:
            try:
                self.trigger_pwm.stop()
            except:
                pass
                
        # Call parent cleanup
        super().cleanup()
        
        print("Water gun controller cleanup complete")

# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Water Gun Controller Test')
    parser.add_argument('--pan-pin', type=int, default=18)
    parser.add_argument('--tilt-pin', type=int, default=19)
    parser.add_argument('--trigger-pin', type=int, default=20)
    parser.add_argument('--test', choices=['trigger', 'calibrate', 'full'], default='trigger')
    
    args = parser.parse_args()
    
    print("🔫 Water Gun Controller Test")
    
    try:
        controller = WaterGunController(args.pan_pin, args.tilt_pin, args.trigger_pin)
        
        if args.test == 'trigger':
            controller.test_trigger()
        elif args.test == 'calibrate':
            controller.calibrate_trigger()
        elif args.test == 'full':
            print("Testing full system...")
            controller.arm_system()
            
            # Simulate target lock and fire
            print("Simulating target at center...")
            for i in range(25):  # 2.5 seconds at 10Hz
                controller.check_target_lock(640, 480, 320, 240)
                time.sleep(0.1)
                
            if controller.target_locked:
                controller.manual_fire()
                
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'controller' in locals():
            controller.cleanup()
