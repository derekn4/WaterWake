#!/usr/bin/env python3
"""
Raspberry Pi Servo Server
Receives head tracking data from Windows client and controls servo motors
"""

import json
import socket
import threading
import time
import signal
import sys
from dataclasses import dataclass
from typing import Optional
import os

# Import controller — try Arduino serial first, then GPIO, then simulation
SERVO_BACKEND = "simulation"

try:
    from serial_servo_controller import SerialServoController
    SERVO_BACKEND = "serial"
except ImportError:
    pass

if SERVO_BACKEND == "simulation":
    try:
        from servo_controller import ServoController
        SERVO_BACKEND = "gpio"
    except ImportError:
        print("Warning: no servo controller found, running in simulation mode")

SERVO_AVAILABLE = SERVO_BACKEND != "simulation"

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

class ServoServer:
    """TCP server that receives tracking data and controls servos"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8888,
                 pan_pin: int = 18, tilt_pin: int = 19, arduino_port: str = ""):
        self.host = host
        self.port = port
        self.pan_pin = pan_pin
        self.tilt_pin = tilt_pin
        self.arduino_port = arduino_port
        
        # Server socket
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.running = False
        
        # Servo controller
        self.servo_controller = None
        self.servo_available = SERVO_AVAILABLE
        
        # Tracking state
        self.last_tracking_data = None
        self.last_update_time = 0
        self.connection_timeout = 5.0  # Seconds
        self.servo_timeout = 2.0  # Return to center if no data for this long
        
        # Statistics
        self.messages_received = 0
        self.last_stats_time = time.time()
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\nShutting down servo server...")
        self.shutdown()
        sys.exit(0)
        
    def initialize_servo_controller(self):
        """Initialize servo controller — Arduino serial first, then GPIO, then simulation."""

        # Try Arduino serial
        if SERVO_BACKEND in ("serial", "simulation"):
            try:
                self.servo_controller = SerialServoController(port=self.arduino_port)
                print("Servo controller initialized (Arduino serial)")
                return True
            except Exception as e:
                print(f"Arduino serial init failed: {e}, trying next backend...")

        # Try GPIO
        try:
            from servo_controller import ServoController as GPIOController
            self.servo_controller = GPIOController(self.pan_pin, self.tilt_pin)
            print(f"Servo controller initialized (GPIO) - Pan: GPIO{self.pan_pin}, Tilt: GPIO{self.tilt_pin}")
            return True
        except Exception as e:
            print(f"GPIO init failed: {e}")

        print("Running in simulation mode")
        self.servo_controller = None
        return False
            
    def start_server(self):
        """Start the TCP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            
            print(f"Servo server listening on {self.host}:{self.port}")
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
            print(f"Client connected from {self.client_address}")
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
        print(f"Received command: {command}")
        
        if command == 'center':
            if self.servo_controller:
                self.servo_controller.move_to_center()
                print("Servos centered")
            else:
                print("Simulated: Servos centered")
                
        elif command == 'reset':
            print("Reset command received")
            # Could add reset logic here
            
        else:
            print(f"Unknown command: {command}")
            
    def process_tracking_data(self, data: TrackingData):
        """Process tracking data and update servos"""
        self.last_tracking_data = data
        self.last_update_time = time.time()
        
        if data.tracking and data.confidence > 0.1:
            # Update servo positions
            if self.servo_controller:
                try:
                    self.servo_controller.track_target(
                        data.frame_width,
                        data.frame_height,
                        data.target_x,
                        data.target_y
                    )
                except Exception as e:
                    print(f"Error updating servo position: {e}")
            else:
                # Simulation mode
                pan_angle = 90 + ((data.frame_width/2 - data.target_x) / data.frame_width) * 90
                tilt_angle = 90 + ((data.frame_height/2 - data.target_y) / data.frame_height) * 90
                print(f"Simulated servo update: Pan={pan_angle:.1f}°, Tilt={tilt_angle:.1f}°")
        else:
            # No tracking or low confidence - could implement search pattern here
            pass
            
    def monitor_connection(self):
        """Monitor connection and handle timeouts"""
        while self.running:
            current_time = time.time()
            
            # Check for servo timeout (return to center if no data)
            if (self.last_update_time > 0 and 
                current_time - self.last_update_time > self.servo_timeout):
                
                if self.servo_controller:
                    try:
                        self.servo_controller.move_to_center()
                        print("No tracking data - servos returned to center")
                    except Exception as e:
                        print(f"Error centering servos: {e}")
                else:
                    print("Simulated: No tracking data - servos returned to center")
                    
                self.last_update_time = 0  # Reset to avoid repeated centering
                
            # Display statistics
            if current_time - self.last_stats_time > 5.0:
                print(f"Messages received: {self.messages_received}")
                self.last_stats_time = current_time
                
            time.sleep(0.5)
            
    def run(self):
        """Main server loop"""
        print("Starting Raspberry Pi servo server...")
        
        # Initialize servo controller
        self.initialize_servo_controller()
        
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
                            print("Client disconnected")
                            break
                            
                        buffer += data
                        
                        # Process complete messages (newline-delimited)
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            if line.strip():
                                self.handle_client_data(line)
                                
                except socket.timeout:
                    print("Client connection timeout")
                except Exception as e:
                    print(f"Error handling client: {e}")
                finally:
                    if self.client_socket:
                        self.client_socket.close()
                        self.client_socket = None
                    print("Client connection closed")
                    
        except KeyboardInterrupt:
            print("\nServer interrupted by user")
        finally:
            self.shutdown()
            
    def shutdown(self):
        """Shutdown server and cleanup resources"""
        print("Shutting down server...")
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
                
        # Cleanup servo controller
        if self.servo_controller:
            try:
                self.servo_controller.cleanup()
            except:
                pass
                
        print("Server shutdown complete")

def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Servo Server for Raspberry Pi')
    parser.add_argument('--host', type=str, default='0.0.0.0', 
                       help='Server host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8888, 
                       help='Server port (default: 8888)')
    parser.add_argument('--pan-pin', type=int, default=18, 
                       help='GPIO pin for pan servo (default: 18)')
    parser.add_argument('--tilt-pin', type=int, default=19,
                       help='GPIO pin for tilt servo (default: 19)')
    parser.add_argument('--arduino-port', type=str, default='',
                       help='Arduino serial port (e.g. /dev/ttyACM0). Empty = auto-detect.')

    args = parser.parse_args()

    print("=== Raspberry Pi Servo Server ===")
    print(f"Server: {args.host}:{args.port}")
    print(f"Backend: {SERVO_BACKEND}")
    if SERVO_BACKEND == "serial":
        port_display = args.arduino_port or "(auto-detect)"
        print(f"Arduino port: {port_display}")
    else:
        print(f"Pan servo: GPIO{args.pan_pin}")
        print(f"Tilt servo: GPIO{args.tilt_pin}")

    # Create and run server
    server = ServoServer(args.host, args.port, args.pan_pin, args.tilt_pin, args.arduino_port)
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.shutdown()

if __name__ == "__main__":
    main()
