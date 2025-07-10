"""
Shared network configuration for servo tracker system
"""

# Network Settings
DEFAULT_PI_HOST = "192.168.1.100"  # Change to your Pi's IP address
DEFAULT_PORT = 8888
CONNECTION_TIMEOUT = 5.0  # seconds
RECONNECT_DELAY = 2.0  # seconds

# Data transmission settings
SEND_INTERVAL = 0.05  # Minimum time between updates (50ms = 20 FPS max)
SERVO_TIMEOUT = 2.0   # Return to center if no data for this long

# Message format version
PROTOCOL_VERSION = "1.0"

# GPIO Pin defaults
DEFAULT_PAN_PIN = 18
DEFAULT_TILT_PIN = 19

# Servo configuration
SERVO_FREQUENCY = 50  # PWM frequency in Hz
SERVO_MIN_ANGLE = 0
SERVO_MAX_ANGLE = 180
SERVO_CENTER_ANGLE = 90

# Tracking parameters
MAX_LOST_FRAMES = 30
BBOX_PADDING = 30
MIN_CONFIDENCE = 0.1

# Camera settings
DEFAULT_CAMERA_INDEX = 0

def get_pi_ip():
    """
    Helper function to get Pi IP address
    You can modify this to automatically detect or use a config file
    """
    return DEFAULT_PI_HOST

def validate_message(message):
    """
    Validate incoming message format
    """
    required_fields = ['target_x', 'target_y', 'frame_width', 'frame_height', 'tracking', 'timestamp']
    
    if isinstance(message, dict):
        if 'command' in message:
            # Command message
            return 'timestamp' in message
        else:
            # Tracking data message
            return all(field in message for field in required_fields)
    
    return False

def create_tracking_message(target_x, target_y, frame_width, frame_height, tracking, confidence=1.0):
    """
    Create a properly formatted tracking message
    """
    import time
    
    return {
        'target_x': int(target_x),
        'target_y': int(target_y),
        'frame_width': int(frame_width),
        'frame_height': int(frame_height),
        'tracking': bool(tracking),
        'timestamp': time.time(),
        'confidence': float(confidence),
        'protocol_version': PROTOCOL_VERSION
    }

def create_command_message(command):
    """
    Create a properly formatted command message
    """
    import time
    
    return {
        'command': str(command),
        'timestamp': time.time(),
        'protocol_version': PROTOCOL_VERSION
    }
