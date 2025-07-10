# Distributed Servo Head Tracker

A distributed head tracking system that uses computer vision to detect and track faces, then controls servo motors to aim towards the detected target. The system is split between a Windows PC (for fast face detection) and a Raspberry Pi (for servo control).

## 🎯 Features

- **Distributed Architecture**: Windows PC handles computationally intensive face detection, Raspberry Pi controls servos
- **Real-time Tracking**: Fast face detection and smooth servo movement
- **Network Communication**: TCP-based communication between Windows and Pi
- **Automatic Reconnection**: Robust network handling with auto-reconnect
- **Configurable**: Easy to customize GPIO pins, network settings, and tracking parameters
- **Graceful Fallback**: System handles disconnections and lost tracking gracefully

## 🏗️ System Architecture

```
┌─────────────────┐    Network     ┌─────────────────┐
│   Windows PC    │◄──────────────►│  Raspberry Pi   │
│                 │   TCP/JSON     │                 │
│ • Face Detection│                │ • Servo Control │
│ • Head Tracking │                │ • TCP Server    │
│ • Camera Input  │                │ • GPIO Control  │
│ • TCP Client    │                │                 │
└─────────────────┘                └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Windows PC with camera
- Raspberry Pi 3B+ or newer
- 2x Servo motors (standard hobby servos like SG90)
- Network connection between PC and Pi

### 1. Raspberry Pi Setup
```bash
# Copy files to Pi
scp -r servo_tracker/raspberry_pi/* pi@your-pi-ip:~/servo_tracker/
scp -r servo_tracker/shared/* pi@your-pi-ip:~/servo_tracker/

# Install dependencies
ssh pi@your-pi-ip
cd ~/servo_tracker
pip3 install -r requirements.txt

# Run servo server
python3 servo_server.py
```

### 2. Windows PC Setup
```bash
# Install dependencies
cd servo_tracker/windows_client
pip install -r requirements.txt

# Run head tracker client
python head_tracker_client.py --pi-host YOUR_PI_IP_ADDRESS
```

## 📁 Project Structure

```
servo_tracker/
├── windows_client/           # Windows face detection client
│   ├── head_tracker_client.py
│   └── requirements.txt
├── raspberry_pi/            # Raspberry Pi servo server
│   ├── servo_server.py
│   ├── servo_controller.py
│   ├── servo_head_tracker.py  # Standalone version
│   └── requirements.txt
├── shared/                  # Shared configuration
│   ├── network_config.py
│   └── servo_config.py
├── tests/                   # Testing utilities
│   └── test_servos.py
├── docs/                    # Documentation
│   ├── DISTRIBUTED_SETUP.md
│   └── SERVO_TRACKER_README.md
└── README.md               # This file
```

## 🔧 Hardware Setup

### Servo Connections
Connect servos to Raspberry Pi GPIO pins:

| Servo | GPIO Pin | Purpose |
|-------|----------|---------|
| Pan (Horizontal) | GPIO 18 | Left/Right movement |
| Tilt (Vertical) | GPIO 19 | Up/Down movement |

### Wiring Diagram
```
Raspberry Pi GPIO:
┌─────────────────┐
│     Pan Servo   │
├─────────────────┤
│ Red    → 5V     │
│ Brown  → GND    │
│ Orange → GPIO18 │
└─────────────────┘

┌─────────────────┐
│    Tilt Servo   │
├─────────────────┤
│ Red    → 5V     │
│ Brown  → GND    │
│ Orange → GPIO19 │
└─────────────────┘
```

## 🎮 Controls

### Windows Client
- `q`: Quit application
- `r`: Reset tracking (force re-detection)
- `c`: Send center command to Pi
- `n`: Toggle network connection

### Raspberry Pi Server
- `Ctrl+C`: Shutdown server gracefully

## ⚙️ Configuration

### Network Settings
Edit `servo_tracker/shared/network_config.py`:
```python
DEFAULT_PI_HOST = "192.168.1.100"  # Your Pi's IP
DEFAULT_PORT = 8888
```

### Servo Settings
Edit `servo_tracker/shared/servo_config.py`:
```python
PAN_PIN = 18      # Pan servo GPIO pin
TILT_PIN = 19     # Tilt servo GPIO pin
PAN_CENTER = 90   # Center position for pan
TILT_CENTER = 90  # Center position for tilt
```

## 🔍 Testing

### Test Servos (on Raspberry Pi)
```bash
cd servo_tracker/tests
python3 test_servos.py --test interactive
```

### Test Face Detection (on Windows)
```bash
# Test original head detection
python head_detection.py
```

## 📖 Documentation

- **[Distributed Setup Guide](docs/DISTRIBUTED_SETUP.md)**: Comprehensive setup instructions
- **[Original Servo Tracker README](docs/SERVO_TRACKER_README.md)**: Standalone version documentation

## 🛠️ Troubleshooting

### Common Issues

**Connection Problems:**
- Verify Pi IP address: `hostname -I`
- Check network connectivity: `ping your-pi-ip`
- Ensure firewall allows port 8888

**Servo Issues:**
- Test servo connections with `test_servos.py`
- Check power supply (servos need adequate power)
- Verify GPIO permissions: `sudo usermod -a -G gpio $USER`

**Performance Issues:**
- Use Ethernet instead of WiFi for stability
- Reduce camera resolution for better performance
- Adjust `SEND_INTERVAL` in network config

## 🔄 Why Distributed?

This distributed approach solves several problems:

1. **Performance**: Raspberry Pi 3 can be slow for real-time face detection
2. **Flexibility**: Easy to upgrade either component independently
3. **Scalability**: Can support multiple cameras or servo systems
4. **Development**: Test face detection and servo control separately

## 🚀 Advanced Features

- **Auto-reconnection**: Handles network disconnections gracefully
- **Rate limiting**: Prevents servo jitter with configurable update rates
- **Timeout handling**: Returns to center position when tracking is lost
- **Command system**: Send commands from Windows to Pi
- **Statistics**: Monitor message rates and connection status

## 📋 Requirements

### Windows PC
- Python 3.7+
- OpenCV
- dlib
- NumPy
- Camera (USB or built-in)

### Raspberry Pi
- Raspberry Pi 3B+ or newer
- Raspbian/Raspberry Pi OS
- Python 3.7+
- RPi.GPIO
- 2x Servo motors
- Adequate power supply

## 🤝 Contributing

Feel free to improve this project by:
- Adding support for different servo types
- Implementing PID control for smoother tracking
- Adding web interface for remote control
- Optimizing performance for different hardware

## 📄 License

This project is open source. Use and modify as needed for your projects.

---

**Need Help?** Check the [troubleshooting guide](docs/DISTRIBUTED_SETUP.md#troubleshooting) or test components individually to isolate issues.
