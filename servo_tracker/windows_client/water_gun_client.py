#!/usr/bin/env python3
"""
Enhanced Windows Head Detection Client with Water Gun Controls
Includes additional commands for arming/disarming the water gun system
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

class WaterGunNetworkClient:
    """Enhanced network client with water gun commands"""
    
    def __init__(self, pi_host: str = "192.168.1.100", pi_port: int = 8888):
        self.pi_host = pi_host
        self.pi_port = pi_port
        self.socket = None
        self.connected = False
        self.reconnect_delay = 2.0
        self.last_send_time = 0
        self.send_interval = 0.05
        
    def connect(self):
        """Connect to Raspberry Pi server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.pi_host, self.pi_port))
            self.connected = True
            print(f"🔗 Connected to Water Gun Pi at {self.pi_host}:{self.pi_port}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Pi: {e}")
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
        
        if current_time - self.last_send_time < self.send_interval:
            return True
            
        if not self.connected:
            return False
            
        try:
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
            print(f"❌ Error sending data: {e}")
            self.connected = False
            return False
            
    def send_command(self, command: str) -> bool:
        """Send command to Pi"""
        if not self.connected:
            return False
            
        try:
            message = {'command': command, 'timestamp': time.time()}
            json_data = json.dumps(message) + '\n'
            self.socket.send(json_data.encode('utf-8'))
            print(f"📤 Sent command: {command}")
            return True
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            self.connected = False
            return False

class WaterGunTrackerClient:
    """Enhanced head tracking client with water gun controls"""
    
    def __init__(self, pi_host: str = "192.168.1.100", pi_port: int = 8888):
        # Network client
        self.network_client = WaterGunNetworkClient(pi_host, pi_port)
        
        # Face detection
        self.face_detector = dlib.get_frontal_face_detector()
        
        # Camera
        self.video_capture = cv2.VideoCapture(0)
        self.frame_width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"📷 Camera resolution: {self.frame_width}x{self.frame_height}")
        
        # Tracking variables
        self.tracker = None
        self.tracking = False
        self.lost_track_counter = 0
        self.max_lost_frames = 30
        
        # Water gun state
        self.system_armed = False
        self.target_locked = False
        self.lock_on_progress = 0.0
        
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
        print("\n🛑 Shutting down water gun tracker client...")
        self.cleanup()
        sys.exit(0)
        
    def start_reconnect_thread(self):
        """Start background thread for reconnection attempts"""
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            return
            
        def reconnect_loop():
            while self.auto_reconnect and not self.network_client.connected:
                print("🔄 Attempting to reconnect to Pi...")
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
        
        if current_time - self.last_fps_display > 1.0:
            fps = self.fps_counter / (current_time - self.fps_start_time)
            status = "ARMED" if self.system_armed else "DISARMED"
            print(f"📊 FPS: {fps:.1f} | Connected: {self.network_client.connected} | Status: {status}")
            self.fps_counter = 0
            self.fps_start_time = current_time
            self.last_fps_display = current_time
            
    def draw_water_gun_ui(self, frame):
        """Draw water gun specific UI elements"""
        # System status
        status_color = (0, 255, 0) if self.system_armed else (0, 0, 255)
        status_text = "ARMED" if self.system_armed else "DISARMED"
        cv2.putText(frame, f"System: {status_text}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Connection status
        conn_color = (0, 255, 0) if self.network_client.connected else (0, 0, 255)
        conn_status = "Connected" if self.network_client.connected else "Disconnected"
        cv2.putText(frame, f"Pi: {conn_status}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, conn_color, 2)
        
        # Target lock indicator
        if self.target_locked:
            cv2.putText(frame, "TARGET LOCKED", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        elif self.lock_on_progress > 0:
            progress_text = f"Locking... {self.lock_on_progress:.1%}"
            cv2.putText(frame, progress_text, (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Draw firing zone (center area)
        center_x = self.frame_width // 2
        center_y = self.frame_height // 2
        tolerance = 30
        
        # Draw firing zone rectangle
        zone_color = (0, 255, 255) if self.system_armed else (128, 128, 128)
        cv2.rectangle(frame, 
                     (center_x - tolerance, center_y - tolerance),
                     (center_x + tolerance, center_y + tolerance),
                     zone_color, 2)
        
        # Draw center crosshair
        cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (255, 255, 255), 1)
        cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (255, 255, 255), 1)
        
    def run(self):
        """Main tracking loop"""
        print("🚀 Starting Water Gun Head Tracker Client...")
        print(f"🎯 Target Pi: {self.network_client.pi_host}:{self.network_client.pi_port}")
        print("\n🎮 Controls:")
        print("  q: Quit")
        print("  r: Reset tracking")
        print("  c: Center servos")
        print("  a: ARM water gun system")
        print("  d: DISARM water gun system")
        print("  f: Manual fire (if armed)")
        print("  e: Emergency stop")
        print("  n: Toggle network connection")
        print("  s: Request status from Pi")
        
        # Initial connection attempt
        if not self.network_client.connect():
            print("❌ Failed to connect initially, will retry in background...")
            self.start_reconnect_thread()
            
        while True:
            ret, frame = self.video_capture.read()
            if not ret:
                print("❌ Failed to read from camera")
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
                    print("👤 Face detected and tracking started")
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
                    rect_color = (0, 255, 0) if not self.system_armed else (0, 255, 255)
                    cv2.rectangle(frame, (startX, startY), (endX, endY), rect_color, 2)
                    cv2.circle(frame, (center_x, center_y), 5, rect_color, -1)
                    
                    # Display tracking info
                    info_text = f"Tracking: ({center_x}, {center_y})"
                    cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, rect_color, 2)
                    
                    # Check if target is in firing zone
                    frame_center_x = self.frame_width // 2
                    frame_center_y = self.frame_height // 2
                    distance_from_center = ((center_x - frame_center_x)**2 + (center_y - frame_center_y)**2)**0.5
                    
                    if distance_from_center < 30:  # Within firing tolerance
                        cv2.putText(frame, "IN FIRING ZONE", (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
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
                        print("❌ Tracking lost, switching back to detection mode")

            # Draw water gun UI
            self.draw_water_gun_ui(frame)

            # Display frame
            cv2.imshow('Water Gun Tracker Client', frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                # Reset tracking
                self.tracking = False
                self.tracker = None
                self.lost_track_counter = 0
                print("🔄 Tracking reset")
            elif key == ord('c'):
                # Center servos
                self.network_client.send_command('center')
            elif key == ord('a'):
                # Arm system
                if self.network_client.send_command('arm'):
                    self.system_armed = True
                    print("🔫 System ARMED")
            elif key == ord('d'):
                # Disarm system
                if self.network_client.send_command('disarm'):
                    self.system_armed = False
                    print("🛡️ System DISARMED")
            elif key == ord('f'):
                # Manual fire
                self.network_client.send_command('manual_fire')
                print("💥 Manual fire command sent")
            elif key == ord('e'):
                # Emergency stop
                if self.network_client.send_command('emergency_stop'):
                    self.system_armed = False
                    print("🚨 EMERGENCY STOP")
            elif key == ord('s'):
                # Request status
                self.network_client.send_command('status')
                print("📊 Status request sent")
            elif key == ord('n'):
                # Toggle network connection
                if self.network_client.connected:
                    self.network_client.disconnect()
                    print("🔌 Disconnected from Pi")
                else:
                    if self.network_client.connect():
                        print("🔗 Reconnected to Pi")
                    else:
                        print("❌ Failed to reconnect")

        self.cleanup()
        
    def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up resources...")
        
        # Disarm system before shutdown
        if self.system_armed:
            self.network_client.send_command('disarm')
        
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
    
    parser = argparse.ArgumentParser(description='Water Gun Head Tracker Client')
    parser.add_argument('--pi-host', type=str, default='192.168.1.100', 
                       help='Raspberry Pi IP address (default: 192.168.1.100)')
    parser.add_argument('--pi-port', type=int, default=8888, 
                       help='Raspberry Pi port (default: 8888)')
    parser.add_argument('--camera', type=int, default=0, 
                       help='Camera index (default: 0)')
    
    args = parser.parse_args()
    
    print("🔫 === Water Gun Head Tracker Client ===")
    print(f"🎯 Target Pi: {args.pi_host}:{args.pi_port}")
    print(f"📷 Camera: {args.camera}")
    print("⚠️  SAFETY REMINDER: This is a water gun system!")
    print("    Always ensure safe operation and proper supervision.")
    
    # Create and run client
    client = WaterGunTrackerClient(args.pi_host, args.pi_port)
    
    # Override camera if specified
    if args.camera != 0:
        client.video_capture.release()
        client.video_capture = cv2.VideoCapture(args.camera)
        client.frame_width = int(client.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        client.frame_height = int(client.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    try:
        client.run()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.cleanup()

if __name__ == "__main__":
    main()
