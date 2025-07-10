# Distributed Servo Head Tracker Setup Guide

This guide explains how to set up the distributed head tracking system where Windows PC handles face detection and Raspberry Pi controls the servos.

## System Architecture

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

## Benefits

- **Performance**: Fast face detection on powerful Windows PC
- **Responsiveness**: Dedicated servo control on Pi
- **Flexibility**: Easy to modify or replace either component
- **Scalability**: Can support multiple cameras or servo systems

## Quick Start

### 1. Raspberry Pi Setup

```bash
# Copy files to Pi
scp -r servo_tracker/raspberry_pi/* pi@your-pi-ip:~/servo_tracker/
scp -r servo_tracker/shared/* pi@your-pi-ip:~/servo_tracker/

# SSH to Pi and install dependencies
ssh pi@your-pi-ip
cd ~/servo_tracker
pip3 install RPi.GPIO

# Run the servo server
python3 servo_server.py
```

### 2. Windows PC Setup

```bash
# Navigate to Windows client directory
cd servo_tracker/windows_client

# Install dependencies (if not already installed)
pip install opencv-python dlib numpy

# Update Pi IP address in the client or use command line
python head_tracker_client.py --pi-host YOUR_PI_IP_ADDRESS
```

## Detailed Setup Instructions

### Raspberry Pi Configuration

#### 1. Hardware Setup
Connect servos to Raspberry Pi:
- **Pan Servo**: Signal → GPIO18, Power → 5V, Ground → GND
- **Tilt Servo**: Signal → GPIO19, Power → 5V, Ground → GND

#### 2. Software Installation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
pip3 install RPi.GPIO

# Enable GPIO (if needed)
sudo raspi-config
# Navigate to: Interface Options → GPIO → Enable
```

#### 3. Network Configuration
```bash
# Find Pi's IP address
hostname -I

# Optional: Set static IP
sudo nano /etc/dhcpcd.conf
# Add:
# interface wlan0
# static ip_address=192.168.1.100/24
# static routers=192.168.1.1
# static domain_name_servers=192.168.1.1
```

#### 4. Run Servo Server
```bash
# Basic usage
python3 servo_server.py

# Custom configuration
python3 servo_server.py --host 0.0.0.0 --port 8888 --pan-pin 18 --tilt-pin 19

# Run as service (optional)
sudo nano /etc/systemd/system/servo-tracker.service
```

### Windows PC Configuration

#### 1. Install Dependencies
```bash
# Using pip
pip install opencv-python dlib numpy

# Or using conda
conda install opencv dlib numpy
```

#### 2. Configure Network
Edit `servo_tracker/shared/network_config.py`:
```python
DEFAULT_PI_HOST = "192.168.1.100"  # Your Pi's IP address
DEFAULT_PORT = 8888
```

#### 3. Run Head Tracker Client
```bash
# Basic usage
python head_tracker_client.py

# Custom configuration
python head_tracker_client.py --pi-host 192.168.1.100 --pi-port 8888 --camera 0
```

## Network Protocol

### Message Format

#### Tracking Data Message
```json
{
    "target_x": 320,
    "target_y": 240,
    "frame_width": 640,
    "frame_height": 480,
    "tracking": true,
    "timestamp": 1641234567.89,
    "confidence": 0.95,
    "protocol_version": "1.0"
}
```

#### Command Message
```json
{
    "command": "center",
    "timestamp": 1641234567.89,
    "protocol_version": "1.0"
}
```

### Available Commands
- `center`: Move servos to center position
- `reset`: Reset tracking system

## Configuration Options

### Servo Server (Pi) Options
```bash
python3 servo_server.py --help

Options:
  --host HOST          Server host address (default: 0.0.0.0)
  --port PORT          Server port (default: 8888)
  --pan-pin PIN        GPIO pin for pan servo (default: 18)
  --tilt-pin PIN       GPIO pin for tilt servo (default: 19)
```

### Head Tracker Client (Windows) Options
```bash
python head_tracker_client.py --help

Options:
  --pi-host HOST       Raspberry Pi IP address (default: 192.168.1.100)
  --pi-port PORT       Raspberry Pi port (default: 8888)
  --camera INDEX       Camera index (default: 0)
```

## Runtime Controls

### Windows Client Controls
- `q`: Quit application
- `r`: Reset tracking (force re-detection)
- `c`: Send center command to Pi
- `n`: Toggle network connection

### Raspberry Pi Server
- `Ctrl+C`: Shutdown server gracefully

## Troubleshooting

### Connection Issues

**Problem**: Client can't connect to Pi
```bash
# Check Pi IP address
hostname -I

# Test network connectivity
ping your-pi-ip

# Check if server is running
netstat -an | grep 8888

# Check firewall (if enabled)
sudo ufw status
```

**Problem**: Connection drops frequently
- Check WiFi signal strength
- Increase `CONNECTION_TIMEOUT` in config
- Use Ethernet connection for stability

### Performance Issues

**Problem**: Servo movement is jittery
- Increase `SEND_INTERVAL` in config
- Check power supply to servos
- Reduce `MAX_STEP` in servo controller

**Problem**: High latency
- Use Ethernet instead of WiFi
- Reduce camera resolution
- Optimize network settings

### Hardware Issues

**Problem**: Servos not moving
```bash
# Test servo connections
python3 ../tests/test_servos.py

# Check GPIO permissions
sudo usermod -a -G gpio $USER

# Verify power supply
# Measure voltage at servo power pins
```

**Problem**: Servo movement range incorrect
- Calibrate servo center positions
- Adjust angle limits in config
- Check servo specifications

## Advanced Configuration

### Auto-Start Services

#### Raspberry Pi Service
```bash
# Create service file
sudo nano /etc/systemd/system/servo-tracker.service

[Unit]
Description=Servo Head Tracker Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/servo_tracker
ExecStart=/usr/bin/python3 servo_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

# Enable service
sudo systemctl enable servo-tracker.service
sudo systemctl start servo-tracker.service
```

#### Windows Auto-Start
Create a batch file or use Task Scheduler to auto-start the client.

### Network Security

#### Basic Security
```bash
# Pi: Restrict server to specific interface
python3 servo_server.py --host 192.168.1.100

# Use firewall rules
sudo ufw allow from 192.168.1.0/24 to any port 8888
```

#### Advanced Security
- Use VPN for remote access
- Implement authentication tokens
- Use encrypted communication (TLS)

## Performance Tuning

### Network Optimization
```python
# In network_config.py
SEND_INTERVAL = 0.033  # 30 FPS max
CONNECTION_TIMEOUT = 10.0  # Longer timeout for stability
```

### Servo Optimization
```python
# In servo_controller.py
MAX_STEP = 3  # Smaller steps for smoother movement
STEP_DELAY = 0.01  # Faster stepping
```

### Camera Optimization
```python
# In head_tracker_client.py
# Set camera resolution
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
```

## Monitoring and Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Monitor Network Traffic
```bash
# On Pi
sudo tcpdump -i wlan0 port 8888

# On Windows
netstat -an | findstr 8888
```

### Performance Monitoring
```bash
# Pi CPU/Memory usage
htop

# Network bandwidth
iftop
```

## File Structure

```
servo_tracker/
├── windows_client/
│   └── head_tracker_client.py    # Windows face detection client
├── raspberry_pi/
│   ├── servo_server.py           # Pi servo control server
│   ├── servo_controller.py       # Servo control class
│   └── servo_head_tracker.py     # Original standalone version
├── shared/
│   ├── network_config.py         # Shared configuration
│   └── servo_config.py           # Servo parameters
├── tests/
│   └── test_servos.py            # Servo testing utility
└── docs/
    ├── DISTRIBUTED_SETUP.md      # This file
    └── SERVO_TRACKER_README.md   # Original documentation
```

## Next Steps

1. **Test the basic setup** with both systems on the same network
2. **Calibrate servo positions** using the test utilities
3. **Optimize performance** based on your specific hardware
4. **Add features** like multiple camera support or web interface
5. **Implement security** if deploying in production environment

## Support

For issues or improvements:
1. Check the troubleshooting section above
2. Test components individually
3. Verify network connectivity and configuration
4. Check hardware connections and power supply
