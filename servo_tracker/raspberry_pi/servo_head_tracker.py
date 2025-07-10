import cv2
import dlib
import time
import signal
import sys
from servo_controller import ServoController

class ServoHeadTracker:
    def __init__(self, pan_pin=18, tilt_pin=19):
        """
        Initialize the servo head tracking system
        
        Args:
            pan_pin: GPIO pin for horizontal servo (default: 18)
            tilt_pin: GPIO pin for vertical servo (default: 19)
        """
        # Initialize servo controller
        try:
            self.servo_controller = ServoController(pan_pin, tilt_pin)
            print("Servo controller initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize servo controller: {e}")
            print("Running in simulation mode (no servo control)")
            self.servo_controller = None
        
        # Load face detector from dlib
        self.face_detector = dlib.get_frontal_face_detector()
        
        # Open the webcam
        self.video_capture = cv2.VideoCapture(0)
        
        # Get camera frame dimensions
        self.frame_width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Camera resolution: {self.frame_width}x{self.frame_height}")
        
        # Initialize variables for object tracking
        self.tracker = None
        self.tracking = False
        
        # Tracking parameters
        self.lost_track_counter = 0
        self.max_lost_frames = 30  # Reset tracking after losing target for this many frames
        
        # Performance monitoring
        self.last_servo_update = 0
        self.servo_update_interval = 0.1  # Update servos every 100ms to avoid jitter
        
        # Setup signal handler for clean exit
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\nShutting down servo head tracker...")
        self.cleanup()
        sys.exit(0)
        
    def calculate_target_center(self, bbox):
        """Calculate the center point of the bounding box"""
        startX, startY, w, h = bbox
        center_x = startX + w // 2
        center_y = startY + h // 2
        return center_x, center_y
        
    def update_servo_position(self, center_x, center_y):
        """Update servo positions to track the target"""
        if self.servo_controller is None:
            return
            
        current_time = time.time()
        if current_time - self.last_servo_update < self.servo_update_interval:
            return
            
        try:
            self.servo_controller.track_target(
                self.frame_width, 
                self.frame_height, 
                center_x, 
                center_y
            )
            self.last_servo_update = current_time
        except Exception as e:
            print(f"Error updating servo position: {e}")
            
    def detect_and_track_head(self):
        """Main detection and tracking loop"""
        print("Starting head detection and servo tracking...")
        print("Press 'q' to quit, 'r' to reset tracking, 'c' to center servos")
        
        while True:
            ret, frame = self.video_capture.read()
            if not ret:
                print("Failed to read from camera")
                break

            if not self.tracking:
                # Convert the frame to grayscale for faster processing
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Detect faces in the grayscale frame
                faces = self.face_detector(gray)

                for face in faces:
                    # Get the head region from the frame
                    (startX, startY, endX, endY) = (face.left(), face.top(), face.right(), face.bottom())

                    # Expand the size of the bounding box
                    padding = 30  # Adjust this value as needed
                    startX -= padding
                    startY -= padding
                    endX += padding
                    endY += padding

                    # Make sure the bounding box stays within the frame boundaries
                    startX = max(0, startX)
                    startY = max(0, startY)
                    endX = min(frame.shape[1], endX)
                    endY = min(frame.shape[0], endY)

                    # Initialize the tracker
                    self.tracker = cv2.TrackerKCF_create()
                    bbox = (startX, startY, endX - startX, endY - startY)
                    self.tracker.init(frame, bbox)

                    self.tracking = True
                    self.lost_track_counter = 0
                    print("Face detected and tracking started")
                    break

            else:
                # Update the tracker
                success, bbox = self.tracker.update(frame)
                
                if success:
                    (startX, startY, w, h) = [int(v) for v in bbox]
                    endX = startX + w
                    endY = startY + h
                    
                    # Calculate center of bounding box
                    center_x, center_y = self.calculate_target_center(bbox)
                    
                    # Update servo positions
                    self.update_servo_position(center_x, center_y)
                    
                    # Draw tracking rectangle (green for successful tracking)
                    cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                    
                    # Draw center point
                    cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
                    
                    # Draw crosshair at frame center for reference
                    frame_center_x = self.frame_width // 2
                    frame_center_y = self.frame_height // 2
                    cv2.line(frame, (frame_center_x - 20, frame_center_y), 
                            (frame_center_x + 20, frame_center_y), (255, 255, 255), 1)
                    cv2.line(frame, (frame_center_x, frame_center_y - 20), 
                            (frame_center_x, frame_center_y + 20), (255, 255, 255), 1)
                    
                    # Display tracking info
                    info_text = f"Tracking: ({center_x}, {center_y})"
                    cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    self.lost_track_counter = 0
                else:
                    self.lost_track_counter += 1
                    
                    # Draw red rectangle to indicate lost tracking
                    cv2.putText(frame, f"Lost tracking ({self.lost_track_counter}/{self.max_lost_frames})", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Reset tracking if lost for too long
                    if self.lost_track_counter >= self.max_lost_frames:
                        self.tracking = False
                        self.tracker = None
                        print("Tracking lost, switching back to detection mode")

            # Display the frame with head detection/tracking
            cv2.imshow('Servo Head Tracker', frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                # Reset tracking
                self.tracking = False
                self.tracker = None
                self.lost_track_counter = 0
                print("Tracking reset")
            elif key == ord('c'):
                # Center servos
                if self.servo_controller:
                    self.servo_controller.move_to_center()
                    print("Servos centered")

        self.cleanup()
        
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up resources...")
        
        # Release the webcam
        if hasattr(self, 'video_capture'):
            self.video_capture.release()
            
        # Destroy OpenCV windows
        cv2.destroyAllWindows()
        
        # Clean up servo controller
        if self.servo_controller:
            self.servo_controller.cleanup()
            
    def calibrate_servos(self):
        """Interactive servo calibration mode"""
        if self.servo_controller is None:
            print("Servo controller not available for calibration")
            return
            
        print("\n=== Servo Calibration Mode ===")
        print("Use the following keys:")
        print("  w/s: Tilt up/down")
        print("  a/d: Pan left/right")
        print("  c: Center servos")
        print("  q: Quit calibration")
        print("  Current position will be displayed")
        
        while True:
            key = input("Enter command (w/s/a/d/c/q): ").lower()
            
            if key == 'q':
                break
            elif key == 'w':
                new_tilt = min(self.servo_controller.tilt_max, 
                              self.servo_controller.current_tilt + 10)
                self.servo_controller.move_servo_smooth(
                    self.servo_controller.current_pan, new_tilt)
            elif key == 's':
                new_tilt = max(self.servo_controller.tilt_min, 
                              self.servo_controller.current_tilt - 10)
                self.servo_controller.move_servo_smooth(
                    self.servo_controller.current_pan, new_tilt)
            elif key == 'a':
                new_pan = min(self.servo_controller.pan_max, 
                             self.servo_controller.current_pan + 10)
                self.servo_controller.move_servo_smooth(
                    new_pan, self.servo_controller.current_tilt)
            elif key == 'd':
                new_pan = max(self.servo_controller.pan_min, 
                             self.servo_controller.current_pan - 10)
                self.servo_controller.move_servo_smooth(
                    new_pan, self.servo_controller.current_tilt)
            elif key == 'c':
                self.servo_controller.move_to_center()
                
            print(f"Current position - Pan: {self.servo_controller.current_pan:.1f}°, "
                  f"Tilt: {self.servo_controller.current_tilt:.1f}°")

def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Servo Head Tracker')
    parser.add_argument('--pan-pin', type=int, default=18, 
                       help='GPIO pin for pan servo (default: 18)')
    parser.add_argument('--tilt-pin', type=int, default=19, 
                       help='GPIO pin for tilt servo (default: 19)')
    parser.add_argument('--calibrate', action='store_true', 
                       help='Run servo calibration mode')
    
    args = parser.parse_args()
    
    # Create tracker instance
    tracker = ServoHeadTracker(args.pan_pin, args.tilt_pin)
    
    try:
        if args.calibrate:
            tracker.calibrate_servos()
        else:
            tracker.detect_and_track_head()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        tracker.cleanup()

if __name__ == "__main__":
    main()
