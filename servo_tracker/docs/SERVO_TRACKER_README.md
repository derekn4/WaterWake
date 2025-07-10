# Servo Head Tracker

A Python-based head tracking system that uses computer vision to detect and track faces, then controls servo motors to aim towards the center of the detected face. Perfect for creating automated camera tracking systems, security cameras, or interactive projects.

## Features

- Real-time face detection using dlib
- Object tracking with OpenCV KCF tracker
- Smooth servo movement with configurable parameters
- Automatic re-detection when tracking is lost
- Interactive calibration mode
- Graceful error handling and cleanup
- Configurable GPIO pins and servo parameters

## Hardware Requirements

### Required Components
- Raspberry Pi (3B+ or newer recommended)
- 2x Servo motors (standard hobby servos like SG90, MG996R)
- USB camera or Raspberry Pi camera module
- Jumper wires
- Breadboard or servo mounting hardware
- External power supply for servos (recommended for larger servos)

### Wiring Diagram

```
Raspberry Pi GPIO Connections:
┌─────────────────┐
│     Servo 1     │  Pan (Horizontal)
│   (Left/Right)  │
├─────────────────┤
│ Red    → 5V     │  (or external power)
│ Brown  → GND    │
│ Orange → GPIO18 │  (configurable)
└─────────────────┘

┌─────────────────┐
│     Servo 2     │  Tilt (Vertical)
│    (Up/Down)    │
├─────────────────┤
│ Red    → 5V     │  (or external power)
│ Brown  → GND    │
│ Orange → GPIO19 │  (configurable)
└─────────────────┘
```

**Important Notes:**
- Small servos (SG90) can be powered from Pi's 5V pin
- Larger servos need external power supply
- Always connect grounds together when using external power

## Software Requirements

### System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-dev cmake build-essential
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y libboost-all-dev

# Install dlib dependencies
sudo apt install -y libatlas-base-dev liblapack-dev libblas-dev
sudo apt install -y libhdf5-dev libhdf5-serial-dev libhdf5-103
sudo apt install -y libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5
```

### Python Dependencies
```bash
# Install Python packages
pip3 install opencv-python
pip3 install dlib
pip3 install RPi.GPIO
pip3 install numpy

# Alternative: Install from requirements file
pip3 install -r requirements.txt
```

### Create requirements.txt
```txt
opencv-python>=4.5.0
dlib>=19.22.0
RPi.GPIO>=0.7.0
numpy>=1.19.0
```

## Installation

1. **Clone or download the files:**
   ```bash
   # Copy these files to your Raspberry Pi:
   # - servo_controller.py
   # - servo_head_tracker.py
   # - servo_config.py
   ```

2. **Make files executable:**
   ```bash
   chmod +x servo_head_tracker.py
   ```

3. **Test camera:**
   ```bash
   # Test if camera is working
   python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.read()[0] else 'Camera Error')"
   ```

## Configuration

Edit `servo_config.py` to match your hardware setup:

```python
# GPIO Pin Configuration
PAN_PIN = 18    # Change if using different pins
TILT_PIN = 19

# Servo Angle Limits (adjust for your servos)
PAN_MIN = 0     # Some servos work better with 10-170
PAN_MAX = 180
TILT_MIN = 0
TILT_MAX = 180

# Center Positions (calibrate these!)
PAN_CENTER = 90   # Adjust so camera points forward
TILT_CENTER = 90  # Adjust so camera is level
```

## Usage

### Basic Usage
```bash
# Run the head tracker
python3 servo_head_tracker.py

# Use custom GPIO pins
python3 servo_head_tracker.py --pan-pin 20 --tilt-pin 21
```

### Calibration Mode
```bash
# Run calibration to find correct center positions
python3 servo_head_tracker.py --calibrate
```

In calibration mode:
- `w/s`: Move tilt servo up/down
- `a/d`: Move pan servo left/right  
- `c`: Center both servos
- `q`: Quit calibration

### Runtime Controls
While running the tracker:
- `q`: Quit program
- `r`: Reset tracking (force re-detection)
- `c`: Center servos manually

## Troubleshooting

### Common Issues

**1. "Permission denied" GPIO errors:**
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
# Logout and login again, or run with sudo
```

**2. Camera not found:**
```bash
# Check camera devices
ls /dev/video*
# Try different camera index in servo_config.py
```

**3. Servos not moving:**
- Check wiring connections
- Verify GPIO pin numbers in config
- Test with multimeter (should see ~50Hz PWM signal)
- Try external power supply for servos

**4. Jittery servo movement:**
- Increase `SERVO_UPDATE_INTERVAL` in config
- Decrease `MAX_STEP` for smoother movement
- Check power supply stability

**5. Face detection not working:**
```bash
# Test face detection separately
python3 head_detection.py
```

**6. Import errors:**
```bash
# Install missing dependencies
pip3 install [missing_package]
```

### Performance Optimization

**For better performance:**
- Use lower camera resolution
- Increase `SERVO_UPDATE_INTERVAL`
- Reduce `MAX_LOST_FRAMES` for faster re-detection
- Use Raspberry Pi 4 for better processing power

**Memory issues:**
```bash
# Increase GPU memory split
sudo raspi-config
# Advanced Options → Memory Split → 128
```

## Advanced Configuration

### Custom Servo Types
For continuous rotation servos or different servo specs, modify the `angle_to_duty_cycle` function in `servo_controller.py`:

```python
def angle_to_duty_cycle(self, angle):
    # Standard servo: 1ms-2ms pulse width
    # Modify these values for your servo:
    min_pulse = 1.0  # ms
    max_pulse = 2.0  # ms
    
    pulse_width = min_pulse + (angle / 180.0) * (max_pulse - min_pulse)
    duty_cycle = (pulse_width / 20.0) * 100  # 20ms period for 50Hz
    return duty_cycle
```

### Multiple Camera Support
To use multiple cameras or specific camera:
```python
# In servo_head_tracker.py, modify:
self.video_capture = cv2.VideoCapture(1)  # Use camera 1 instead of 0
```

### Network Control
For remote control, you can extend the system with:
- Flask web interface
- Socket communication
- MQTT integration

## Safety Notes

⚠️ **Important Safety Guidelines:**
- Always test servo movement limits before full operation
- Use appropriate power supply for your servos
- Secure all wiring to prevent shorts
- Mount servos securely to prevent damage
- Never exceed servo specifications
- Add physical stops to prevent over-rotation

## File Structure

```
servo_head_tracker/
├── servo_controller.py      # Servo control class
├── servo_head_tracker.py    # Main tracking application
├── servo_config.py          # Configuration settings
├── head_detection.py        # Original detection code
└── SERVO_TRACKER_README.md  # This file
```

## Contributing

Feel free to improve this project by:
- Adding support for different servo types
- Implementing PID control for smoother tracking
- Adding web interface for remote control
- Optimizing performance for different Pi models

## License

This project is open source. Use and modify as needed for your projects.

---

**Need Help?**
- Check the troubleshooting section above
- Test each component separately
- Verify all connections and power supplies
- Start with calibration mode to ensure servos work correctly
