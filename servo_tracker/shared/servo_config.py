"""
Configuration file for servo head tracker
Adjust these values based on your specific servo setup
"""

# GPIO Pin Configuration
PAN_PIN = 18    # GPIO pin for horizontal servo
TILT_PIN = 19   # GPIO pin for vertical servo

# Servo Angle Limits (adjust based on your servo specifications)
PAN_MIN = 0     # Minimum pan angle (degrees)
PAN_MAX = 180   # Maximum pan angle (degrees)
TILT_MIN = 0    # Minimum tilt angle (degrees)
TILT_MAX = 180  # Maximum tilt angle (degrees)

# Center Positions (adjust to match your physical setup)
PAN_CENTER = 90   # Center position for pan servo
TILT_CENTER = 90  # Center position for tilt servo

# Movement Parameters
MAX_STEP = 5        # Maximum degrees per movement step (smaller = smoother)
STEP_DELAY = 0.02   # Delay between movement steps (seconds)
SERVO_UPDATE_INTERVAL = 0.1  # Minimum time between servo updates (seconds)

# Tracking Parameters
MAX_LOST_FRAMES = 30    # Reset tracking after losing target for this many frames
BBOX_PADDING = 30       # Padding around detected face (pixels)

# PWM Configuration
PWM_FREQUENCY = 50      # PWM frequency in Hz (standard for servos)

# Camera Configuration
CAMERA_INDEX = 0        # Camera device index (usually 0 for default camera)

# Display Options
SHOW_CROSSHAIR = True   # Show crosshair at frame center
SHOW_CENTER_DOT = True  # Show dot at tracked target center
SHOW_TRACKING_INFO = True  # Show tracking coordinates on screen
