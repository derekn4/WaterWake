#!/usr/bin/env python3
"""
Windows Head Detection Client
Detects and tracks heads, then sends coordinate data to Raspberry Pi servo server
"""

import cv2
import dlib
import time
import json
import socket
import threading
import signal
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class TrackingData:
    """Data structure for tracking information"""
    target_x: int
    target_y: int
    frame_width: int
    frame_height: int
    tracking: bool
    timestamp: float
    confidence: float = 1.0

class NetworkClient:
    """Handles network communication with Raspberry Pi"""
    
    def __init__(self, pi_host: str = "192.168.1.100", pi_port: int = 8888):
        self.pi_host = pi_host
        self.pi_port = pi_port
        self.socket = None
        self.connected = False
        self.reconnect_delay = 2.0
        self.last_send_time = 0
        self.send_interval = 0.05  # Send updates every 50ms max
        
    def connect(self):
        """Connect to Raspberry Pi server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.pi_host, self.pi_port))
            self.connected = True
            print(f"Connected to Raspberry Pi at {self.pi_host}:{self.pi_port}")
            return True
        except Exception as e:
            print(f"Failed to connect to Pi: {e}")
            self.connected = False
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
            
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            
    def send_tracking_data(self, data: TrackingData) -> bool:
        """Send tracking data to Pi"""
        current_time = time.time()
        
        # Rate limiting
        if current_time - self.last_send_time < self.send_interval:
            return True
            
        if not self.connected:
            return False
            
        try:
            # Convert to JSON
            message = {
                'target_x': data.target_x,
                'target_y': data.target_y,
                'frame_width': data.frame_width,
                'frame_height': data.frame_height,
                'tracking': data.tracking,
                'timestamp': data.timestamp,
                'confidence': data.confidence
            }
            
            json_data = json.dumps(message) + '\n'
            self.socket.send(json_data.encode('utf-8'))
            self.last_send_time = current_time
            return True
            
        except Exception as e:
            print(f"Error sending data: {e}")
            self.connected = False
            return False
            
    def send_command(self, command: str) -> bool:
        """Send command to Pi (center, reset, etc.)"""
        if not self.connected:
            return False
            
        try:
            message = {'command': command, 'timestamp': time.time()}
            json_data = json.dumps(message) + '\n'
            self.socket.send(json_data.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            self.connected = False
            return False

class HeadTrackerClient:
    """Main head tracking client for Windows"""
    
    def __init__(self, pi_host: str = "192.168.1.100", pi_port: int = 8888):
        # Network client
        self.network_client = NetworkClient(pi_host, pi_port)
        
        # Face detection
        self.face_detector = dlib.get_frontal_face_detector()
        
        # Camera
        self.video_capture = cv2.VideoCapture(0)
        self.frame_width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Camera resolution: {self.frame_width}x{self.frame_height}")
        
        # Tracking variables
        self.tracker = None
        self.tracking = False
        self.lost_track_counter = 0
        self.max_lost_frames = 30
        
        # Performance monitoring
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.last_fps_display = 0
        
        # Connection management
        self.auto_reconnect = True
        self.reconnect_thread = None
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\nShutting down head tracker client...")
        self.cleanup()
        sys.exit(0)
        
    def start_reconnect_thread(self):
        """Start background thread for reconnection attempts"""
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            return
            
        def reconnect_loop():
            while self.auto_reconnect and not self.network_client.connected:
                print("Attempting to reconnect to Pi...")
                if self.network_client.connect():
                    break
                time.sleep(self.network_client.reconnect_delay)
                
        self.reconnect_thread = threading.Thread(target=reconnect_loop, daemon=True)
        self.reconnect_thread.start()
        
    def calculate_target_center(self, bbox) -> Tuple[int, int]:
        """Calculate center point of bounding box"""
        startX, startY, w, h = bbox
        center_x = startX + w // 2
        center_y = startY + h // 2
        return center_x, center_y
        
    def send_tracking_update(self, center_x: int, center_y: int, tracking: bool, confidence: float = 1.0):
        """Send tracking update to Pi"""
        data = TrackingData(
            target_x=center_x,
            target_y=center_y,
            frame_width=self.frame_width,
            frame_height=self.frame_height,
            tracking=tracking,
            timestamp=time.time(),
            confidence=confidence
        )
        
        success = self.network_client.send_tracking_data(data)
        if not success and self.auto_reconnect:
            self.start_reconnect_thread()
            
    def update_fps_counter(self):
        """Update and display FPS"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.last_fps_display > 1.0:  # Update every second
            fps = self.fps_counter / (current_time - self.fps_start_time)
            print(f"FPS: {fps:.1f} | Connected: {self.network_client.connected}")
            self.fps_counter = 0
            self.fps_start_time = current_time
            self.last_fps_display = current_time
            
    def run(self):
        """Main tracking loop"""
        print("Starting head detection client...")
        print(f"Target Pi: {self.network_client.pi_host}:{self.network_client.pi_port}")
        print("Press 'q' to quit, 'r' to reset tracking, 'c' to center servos")
        print("Press 'n' to toggle network connection")
        
        # Initial connection attempt
        if not self.network_client.connect():
            print("Failed to connect initially, will retry in background...")
            self.start_reconnect_thread()
            
        while True:
            ret, frame = self.video_capture.read()
            if not ret:
                print("Failed to read from camera")
                break
                
            # Update FPS counter
            self.update_fps_counter()

            if not self.tracking:
                # Face detection mode
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_detector(gray)

                for face in faces:
                    # Get face region
                    (startX, startY, endX, endY) = (face.left(), face.top(), face.right(), face.bottom())

                    # Expand bounding box
                    padding = 30
                    startX = max(0, startX - padding)
                    startY = max(0, startY - padding)
                    endX = min(frame.shape[1], endX + padding)
                    endY = min(frame.shape[0], endY + padding)

                    # Initialize tracker
                    self.tracker = cv2.TrackerKCF_create()
                    bbox = (startX, startY, endX - startX, endY - startY)
                    self.tracker.init(frame, bbox)

                    self.tracking = True
                    self.lost_track_counter = 0
                    print("Face detected and tracking started")
                    break

            else:
                # Tracking mode
                success, bbox = self.tracker.update(frame)
                
                if success:
                    (startX, startY, w, h) = [int(v) for v in bbox]
                    endX = startX + w
                    endY = startY + h
                    
                    # Calculate center
                    center_x, center_y = self.calculate_target_center(bbox)
                    
                    # Send tracking data to Pi
                    self.send_tracking_update(center_x, center_y, True)
                    
                    # Draw tracking rectangle
                    cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                    cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
                    
                    # Draw crosshair at frame center
                    frame_center_x = self.frame_width // 2
                    frame_center_y = self.frame_height // 2
                    cv2.line(frame, (frame_center_x - 20, frame_center_y), 
                            (frame_center_x + 20, frame_center_y), (255, 255, 255), 1)
                    cv2.line(frame, (frame_center_x, frame_center_y - 20), 
                            (frame_center_x, frame_center_y + 20), (255, 255, 255), 1)
                    
                    # Display info
                    info_text = f"Tracking: ({center_x}, {center_y})"
                    cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Connection status
                    conn_status = "Connected" if self.network_client.connected else "Disconnected"
                    cv2.putText(frame, f"Pi: {conn_status}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                               (0, 255, 0) if self.network_client.connected else (0, 0, 255), 2)
                    
                    self.lost_track_counter = 0
                else:
                    self.lost_track_counter += 1
                    
                    # Send lost tracking update
                    self.send_tracking_update(0, 0, False, 0.0)
                    
                    # Display lost tracking
                    cv2.putText(frame, f"Lost tracking ({self.lost_track_counter}/{self.max_lost_frames})", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Reset if lost too long
                    if self.lost_track_counter >= self.max_lost_frames:
                        self.tracking = False
                        self.tracker = None
                        print("Tracking lost, switching back to detection mode")

            # Display frame
            cv2.imshow('Head Tracker Client (Windows)', frame)

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
                self.network_client.send_command('center')
                print("Center command sent to Pi")
            elif key == ord('n'):
                # Toggle network connection
                if self.network_client.connected:
                    self.network_client.disconnect()
                    print("Disconnected from Pi")
                else:
                    if self.network_client.connect():
                        print("Reconnected to Pi")
                    else:
                        print("Failed to reconnect")

        self.cleanup()
        
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up resources...")
        
        # Stop auto-reconnect
        self.auto_reconnect = False
        
        # Release camera
        if hasattr(self, 'video_capture'):
            self.video_capture.release()
            
        # Close network connection
        self.network_client.disconnect()
            
        # Destroy OpenCV windows
        cv2.destroyAllWindows()

def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Head Tracker Client for Windows')
    parser.add_argument('--pi-host', type=str, default='192.168.1.100', 
                       help='Raspberry Pi IP address (default: 192.168.1.100)')
    parser.add_argument('--pi-port', type=int, default=8888, 
                       help='Raspberry Pi port (default: 8888)')
    parser.add_argument('--camera', type=int, default=0, 
                       help='Camera index (default: 0)')
    
    args = parser.parse_args()
    
    print("=== Head Tracker Client ===")
    print(f"Target Pi: {args.pi_host}:{args.pi_port}")
    print(f"Camera: {args.camera}")
    
    # Create and run client
    client = HeadTrackerClient(args.pi_host, args.pi_port)
    
    # Override camera if specified
    if args.camera != 0:
        client.video_capture.release()
        client.video_capture = cv2.VideoCapture(args.camera)
        client.frame_width = int(client.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        client.frame_height = int(client.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    try:
        client.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.cleanup()

if __name__ == "__main__":
    main()
