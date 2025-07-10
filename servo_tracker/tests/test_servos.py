#!/usr/bin/env python3
"""
Simple servo test script for debugging and verification
Use this to test your servo connections before running the full head tracker
"""

import time
import sys
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("RPi.GPIO not available - running in simulation mode")
    GPIO_AVAILABLE = False

class ServoTester:
    def __init__(self, pan_pin=18, tilt_pin=19):
        self.pan_pin = pan_pin
        self.tilt_pin = tilt_pin
        self.frequency = 50
        
        if GPIO_AVAILABLE:
            self.setup_gpio()
        else:
            print("GPIO not available - commands will be simulated")
            
    def setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pan_pin, GPIO.OUT)
        GPIO.setup(self.tilt_pin, GPIO.OUT)
        
        self.pan_pwm = GPIO.PWM(self.pan_pin, self.frequency)
        self.tilt_pwm = GPIO.PWM(self.tilt_pin, self.frequency)
        
        self.pan_pwm.start(0)
        self.tilt_pwm.start(0)
        print(f"GPIO initialized - Pan: GPIO{self.pan_pin}, Tilt: GPIO{self.tilt_pin}")
        
    def angle_to_duty_cycle(self, angle):
        """Convert angle to duty cycle"""
        angle = max(0, min(180, angle))
        duty_cycle = 2.5 + (angle / 180.0) * 10.0
        return duty_cycle
        
    def set_servo_angle(self, servo_pwm, angle):
        """Set servo to specific angle"""
        if GPIO_AVAILABLE:
            duty_cycle = self.angle_to_duty_cycle(angle)
            servo_pwm.ChangeDutyCycle(duty_cycle)
        else:
            print(f"Simulated: Setting servo to {angle}°")
            
    def test_servo_sweep(self):
        """Test both servos with a sweep pattern"""
        print("\n=== Servo Sweep Test ===")
        print("Both servos will sweep from 0° to 180° and back")
        print("Watch for smooth movement and correct range")
        
        if not GPIO_AVAILABLE:
            print("GPIO not available - simulating sweep")
            for angle in range(0, 181, 10):
                print(f"Simulated: Pan={angle}°, Tilt={angle}°")
                time.sleep(0.1)
            return
            
        try:
            # Sweep forward
            for angle in range(0, 181, 10):
                print(f"Setting servos to {angle}°")
                self.set_servo_angle(self.pan_pwm, angle)
                self.set_servo_angle(self.tilt_pwm, angle)
                time.sleep(0.5)
                
            # Sweep backward
            for angle in range(180, -1, -10):
                print(f"Setting servos to {angle}°")
                self.set_servo_angle(self.pan_pwm, angle)
                self.set_servo_angle(self.tilt_pwm, angle)
                time.sleep(0.5)
                
            # Return to center
            print("Returning to center (90°)")
            self.set_servo_angle(self.pan_pwm, 90)
            self.set_servo_angle(self.tilt_pwm, 90)
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            
    def test_individual_servos(self):
        """Test each servo individually"""
        print("\n=== Individual Servo Test ===")
        
        # Test pan servo
        print("Testing PAN servo (left/right)...")
        angles = [0, 45, 90, 135, 180, 90]  # End at center
        
        for angle in angles:
            print(f"Pan servo: {angle}°")
            if GPIO_AVAILABLE:
                self.set_servo_angle(self.pan_pwm, angle)
            time.sleep(1)
            
        # Test tilt servo
        print("Testing TILT servo (up/down)...")
        for angle in angles:
            print(f"Tilt servo: {angle}°")
            if GPIO_AVAILABLE:
                self.set_servo_angle(self.tilt_pwm, angle)
            time.sleep(1)
            
    def interactive_test(self):
        """Interactive servo control"""
        print("\n=== Interactive Servo Control ===")
        print("Commands:")
        print("  w/s: Tilt up/down")
        print("  a/d: Pan left/right")
        print("  c: Center both servos")
        print("  sweep: Run sweep test")
        print("  q: Quit")
        
        pan_angle = 90
        tilt_angle = 90
        
        # Set initial position
        if GPIO_AVAILABLE:
            self.set_servo_angle(self.pan_pwm, pan_angle)
            self.set_servo_angle(self.tilt_pwm, tilt_angle)
            
        while True:
            print(f"\nCurrent position - Pan: {pan_angle}°, Tilt: {tilt_angle}°")
            command = input("Enter command: ").lower().strip()
            
            if command == 'q':
                break
            elif command == 'w':
                tilt_angle = min(180, tilt_angle + 10)
                if GPIO_AVAILABLE:
                    self.set_servo_angle(self.tilt_pwm, tilt_angle)
            elif command == 's':
                tilt_angle = max(0, tilt_angle - 10)
                if GPIO_AVAILABLE:
                    self.set_servo_angle(self.tilt_pwm, tilt_angle)
            elif command == 'a':
                pan_angle = min(180, pan_angle + 10)
                if GPIO_AVAILABLE:
                    self.set_servo_angle(self.pan_pwm, pan_angle)
            elif command == 'd':
                pan_angle = max(0, pan_angle - 10)
                if GPIO_AVAILABLE:
                    self.set_servo_angle(self.pan_pwm, pan_angle)
            elif command == 'c':
                pan_angle = 90
                tilt_angle = 90
                if GPIO_AVAILABLE:
                    self.set_servo_angle(self.pan_pwm, pan_angle)
                    self.set_servo_angle(self.tilt_pwm, tilt_angle)
                print("Servos centered")
            elif command == 'sweep':
                self.test_servo_sweep()
                # Reset to current position
                if GPIO_AVAILABLE:
                    self.set_servo_angle(self.pan_pwm, pan_angle)
                    self.set_servo_angle(self.tilt_pwm, tilt_angle)
            else:
                print("Unknown command")
                
    def cleanup(self):
        """Clean up GPIO resources"""
        if GPIO_AVAILABLE:
            try:
                self.pan_pwm.stop()
                self.tilt_pwm.stop()
                GPIO.cleanup()
                print("GPIO cleaned up")
            except:
                pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Servo Test Utility')
    parser.add_argument('--pan-pin', type=int, default=18, 
                       help='GPIO pin for pan servo (default: 18)')
    parser.add_argument('--tilt-pin', type=int, default=19, 
                       help='GPIO pin for tilt servo (default: 19)')
    parser.add_argument('--test', choices=['sweep', 'individual', 'interactive'], 
                       default='interactive',
                       help='Test type to run (default: interactive)')
    
    args = parser.parse_args()
    
    print("=== Servo Test Utility ===")
    print(f"Pan servo: GPIO{args.pan_pin}")
    print(f"Tilt servo: GPIO{args.tilt_pin}")
    
    if not GPIO_AVAILABLE:
        print("\nWARNING: RPi.GPIO not available!")
        print("This script will run in simulation mode.")
        print("Install RPi.GPIO with: pip3 install RPi.GPIO")
        print("Or run on a Raspberry Pi with GPIO support.\n")
    
    tester = ServoTester(args.pan_pin, args.tilt_pin)
    
    try:
        if args.test == 'sweep':
            tester.test_servo_sweep()
        elif args.test == 'individual':
            tester.test_individual_servos()
        elif args.test == 'interactive':
            tester.interactive_test()
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        tester.cleanup()
        print("Test completed")

if __name__ == "__main__":
    main()
