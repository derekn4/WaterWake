#!/usr/bin/env python3
"""
Water Gun Servo Server
Enhanced version of servo_server.py with water gun trigger control
"""

import json
import socket
import threading
import time
import signal
import sys
from dataclasses import dataclass
from typing import Optional

# Import water gun controller
try:
    from water_gun_controller import WaterGunController
    WATER_GUN_AVAILABLE = True
except ImportError:
    print("Warning: water_gun_controller not found, falling back to basic servo control")
    try:
        from servo_controller import ServoController
        WATER_GUN_AVAILABLE = False
    except ImportError:
        print("Warning: servo_controller not found, running in simulation mode")
        ServoController = None
        WATER_GUN_AVAILABLE = False

@dataclass
class TrackingData:
    """Data structure for received tracking information"""
    target_x: int
    target_y: int
    frame_width: int
    frame_height: int
    tracking: bool
    timestamp: float
    confidence: float = 1.0

class WaterGunServer:
    """Enhanced TCP server with water gun trigger control"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8888, 
                 pan_pin: int = 18, tilt_pin: int = 19, trigger_pin: int = 20):
        self.host = host
        self.port = port
        self.pan_pin = pan_pin
        self.tilt_pin = tilt_pin
        self.trigger_pin = trigger_pin
        
        # Server socket
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.running = False
        
        # Water gun controller
        self.controller = None
        self.water_gun_available = WATER_GUN_AVAILABLE
        
        # Tracking state
        self.last_tracking_data = None
        self.last_update_time = 0
        self.connection_timeout = 5.0
        self.servo_timeout = 2.0
        
        # Statistics
        self.messages_received = 0
        self.shots_fired = 0
        self.last_stats_time = time.time()
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\nShutting down water gun server...")
        self.shutdown()
        sys.exit(0)
        
    def initialize_controller(self):
        """Initialize water gun controller"""
        if not ServoController:
            print("Servo controller not available - running in simulation mode")
            return False
            
        try:
            if self.water_gun_available:
                self.controller = WaterGunController(self.pan_pin, self.tilt_pin, self.trigger_pin)
                print(f"🔫 Water gun controller initialized")
                print(f"   Pan: GPIO{self.pan_pin}, Tilt: GPIO{self.tilt_pin}, Trigger: GPIO{self.trigger_pin}")
            else:
                self.controller = ServoController(self.pan_pin, self.tilt_pin)
                print(f"Basic servo controller initialized (no trigger control)")
                print(f"   Pan: GPIO{self.pan_pin}, Tilt: GPIO{self.tilt_pin}")
            return True
        except Exception as e:
            print(f"Failed to initialize controller: {e}")
            print("Running in simulation mode")
            self.controller = None
            return False
            
    def start_server(self):
        """Start the TCP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            
            print(f"🌐 Water gun server listening on {self.host}:{self.port}")
            print("Waiting for Windows client connection...")
            
            self.running = True
            return True
            
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False
            
    def accept_client(self):
        """Accept client connection"""
        try:
            self.client_socket, self.client_address = self.server_socket.accept()
            self.client_socket.settimeout(self.connection_timeout)
            print(f"📱 Client connected from {self.client_address}")
            return True
        except Exception as e:
            print(f"Error accepting client: {e}")
            return False
            
    def handle_client_data(self, data: str):
        """Process received data from client"""
        try:
            message = json.loads(data.strip())
            
            # Handle command messages
            if 'command' in message:
                self.handle_command(message['command'])
                return
                
            # Handle tracking data
            tracking_data = TrackingData(
                target_x=message['target_x'],
                target_y=message['target_y'],
                frame_width=message['frame_width'],
                frame_height=message['frame_height'],
                tracking=message['tracking'],
                timestamp=message['timestamp'],
                confidence=message.get('confidence', 1.0)
            )
            
            self.process_tracking_data(tracking_data)
            self.messages_received += 1
            
        except json.JSONDecodeError as e:
            print(f"Invalid JSON received: {e}")
        except KeyError as e:
            print(f"Missing required field in message: {e}")
        except Exception as e:
            print(f"Error processing client data: {e}")
            
    def handle_command(self, command: str):
        """Handle command from client"""
        print(f"📨 Received command: {command}")
        
        if command == 'center':
            if self.controller:
                self.controller.move_to_center()
                print("🎯 Servos centered")
            else:
                print("Simulated: Servos centered")
                
        elif command == 'arm':
            if self.water_gun_available and self.controller:
                self.controller.arm_system()
            else:
                print("🔫 Simulated: System armed")
                
        elif command == 'disarm':
            if self.water_gun_available and self.controller:
                self.controller.disarm_system()
            else:
                print("🛡️ Simulated: System disarmed")
                
        elif command == 'emergency_stop':
            if self.water_gun_available and self.controller:
                self.controller.emergency_stop_trigger()
            else:
                print("🚨 Simulated: Emergency stop")
                
        elif command == 'manual_fire':
            if self.water_gun_available and self.controller:
                if self.controller.manual_fire():
                    self.shots_fired += 1
            else:
                print("💥 Simulated: Manual fire")
                
        elif command == 'status':
            self.send_status_to_client()
            
        elif command == 'reset':
            print("🔄 Reset command received")
            
        else:
            print(f"❓ Unknown command: {command}")
            
    def send_status_to_client(self):
        """Send status back to client"""
        if not self.client_socket:
            return
            
        try:
            if self.water_gun_available and self.controller:
                status = self.controller.get_status()
                status['shots_fired_total'] = self.shots_fired
                status['messages_received'] = self.messages_received
            else:
                status = {
                    'armed': False,
                    'emergency_stop': False,
                    'target_locked': False,
                    'simulation_mode': True,
                    'shots_fired_total': self.shots_fired,
                    'messages_received': self.messages_received
                }
                
            response = {'status': status, 'timestamp': time.time()}
            json_data = json.dumps(response) + '\n'
            self.client_socket.send(json_data.encode('utf-8'))
            
        except Exception as e:
            print(f"Error sending status: {e}")
            
    def process_tracking_data(self, data: TrackingData):
        """Process tracking data and update servos/trigger"""
        self.last_tracking_data = data
        self.last_update_time = time.time()
        
        if data.tracking and data.confidence > 0.1:
            if self.controller:
                try:
                    if self.water_gun_available:
                        # Use enhanced tracking with firing capability
                        old_shots = self.controller.shots_this_minute
                        self.controller.track_and_fire(
                            data.frame_width,
                            data.frame_height,
                            data.target_x,
                            data.target_y
                        )
                        # Check if a shot was fired
                        if self.controller.shots_this_minute > old_shots:
                            self.shots_fired += 1
                    else:
                        # Basic tracking only
                        self.controller.track_target(
                            data.frame_width,
                            data.frame_height,
                            data.target_x,
                            data.target_y
                        )
                except Exception as e:
                    print(f"Error updating controller: {e}")
            else:
                # Simulation mode
                pan_angle = 90 + ((data.frame_width/2 - data.target_x) / data.frame_width) * 90
                tilt_angle = 90 + ((data.frame_height/2 - data.target_y) / data.frame_height) * 90
                
                # Check if target would be centered (for simulation)
                center_x = data.frame_width // 2
                center_y = data.frame_height // 2
                distance_from_center = ((data.target_x - center_x)**2 + (data.target_y - center_y)**2)**0.5
                
                if distance_from_center < 30:  # Within firing tolerance
                    print(f"🎯 Simulated: Target centered - would fire! Pan={pan_angle:.1f}°, Tilt={tilt_angle:.1f}°")
                else:
                    print(f"🔍 Simulated: Tracking - Pan={pan_angle:.1f}°, Tilt={tilt_angle:.1f}°")
                    
    def monitor_connection(self):
        """Monitor connection and handle timeouts"""
        while self.running:
            current_time = time.time()
            
            # Check for servo timeout (return to center if no data)
            if (self.last_update_time > 0 and 
                current_time - self.last_update_time > self.servo_timeout):
                
                if self.controller:
                    try:
                        self.controller.move_to_center()
                        if self.water_gun_available:
                            # Reset target lock when returning to center
                            self.controller.target_locked = False
                            self.controller.lock_on_timer = 0
                        print("⏰ No tracking data - servos returned to center")
                    except Exception as e:
                        print(f"Error centering servos: {e}")
                else:
                    print("⏰ Simulated: No tracking data - servos returned to center")
                    
                self.last_update_time = 0
                
            # Display statistics
            if current_time - self.last_stats_time > 10.0:  # Every 10 seconds
                print(f"📊 Stats: {self.messages_received} messages, {self.shots_fired} shots fired")
                if self.water_gun_available and self.controller:
                    status = self.controller.get_status()
                    print(f"🔫 System: {'ARMED' if status['armed'] else 'DISARMED'}, "
                          f"Target: {'LOCKED' if status['target_locked'] else 'SEARCHING'}")
                self.last_stats_time = current_time
                
            time.sleep(0.5)
            
    def run(self):
        """Main server loop"""
        print("🚀 Starting Water Gun Server...")
        
        # Initialize controller
        self.initialize_controller()
        
        # Start server
        if not self.start_server():
            return
            
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_connection, daemon=True)
        monitor_thread.start()
        
        try:
            while self.running:
                # Accept client connection
                if not self.accept_client():
                    continue
                    
                # Handle client messages
                buffer = ""
                try:
                    while self.running:
                        data = self.client_socket.recv(1024).decode('utf-8')
                        if not data:
                            print("📱 Client disconnected")
                            break
                            
                        buffer += data
                        
                        # Process complete messages (newline-delimited)
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            if line.strip():
                                self.handle_client_data(line)
                                
                except socket.timeout:
                    print("⏰ Client connection timeout")
                except Exception as e:
                    print(f"Error handling client: {e}")
                finally:
                    if self.client_socket:
                        self.client_socket.close()
                        self.client_socket = None
                    print("📱 Client connection closed")
                    
        except KeyboardInterrupt:
            print("\n🛑 Server interrupted by user")
        finally:
            self.shutdown()
            
    def shutdown(self):
        """Shutdown server and cleanup resources"""
        print("🛑 Shutting down server...")
        self.running = False
        
        # Close client connection
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
                
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        # Cleanup controller
        if self.controller:
            try:
                self.controller.cleanup()
            except:
                pass
                
        print("✅ Server shutdown complete")

def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Water Gun Server for Raspberry Pi')
    parser.add_argument('--host', type=str, default='0.0.0.0', 
                       help='Server host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8888, 
                       help='Server port (default: 8888)')
    parser.add_argument('--pan-pin', type=int, default=18, 
                       help='GPIO pin for pan servo (default: 18)')
    parser.add_argument('--tilt-pin', type=int, default=19, 
                       help='GPIO pin for tilt servo (default: 19)')
    parser.add_argument('--trigger-pin', type=int, default=20, 
                       help='GPIO pin for trigger servo (default: 20)')
    
    args = parser.parse_args()
    
    print("🔫 === Water Gun Server ===")
    print(f"🌐 Server: {args.host}:{args.port}")
    print(f"🎯 Pan servo: GPIO{args.pan_pin}")
    print(f"🎯 Tilt servo: GPIO{args.tilt_pin}")
    print(f"🔫 Trigger servo: GPIO{args.trigger_pin}")
    
    # Create and run server
    server = WaterGunServer(args.host, args.port, args.pan_pin, args.tilt_pin, args.trigger_pin)
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        server.shutdown()

if __name__ == "__main__":
    main()
