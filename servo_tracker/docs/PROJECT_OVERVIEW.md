# Water Gun Alarm System - Project Overview

## 🎯 What This Project Does

This is a **distributed water gun alarm system** that automatically tracks your face and shoots water at you when you're detected and centered in the camera view. Perfect for:

- **Alarm Clock**: Wake up with a splash of water!
- **Security System**: Deter intruders with water shots
- **Fun Project**: Interactive water gun that follows faces
- **Learning Tool**: Computer vision + robotics + networking

## 🏗️ System Architecture

### High-Level Overview
```
┌─────────────────────┐    WiFi/Ethernet    ┌─────────────────────┐
│    Windows PC       │◄──────────────────►│   Raspberry Pi      │
│                     │    TCP/JSON         │                     │
│  ┌───────────────┐  │                     │  ┌───────────────┐  │
│  │   Camera      │  │                     │  │   3 Servos    │  │
│  │   Face        │  │                     │  │   • Pan       │  │
│  │   Detection   │  │                     │  │   • Tilt      │  │
│  │   Tracking    │  │                     │  │   • Trigger   │  │
│  └───────────────┘  │                     │  └───────────────┘  │
│                     │                     │                     │
│  Fast Processing    │                     │  Hardware Control   │
│  High FPS           │                     │  GPIO/PWM           │
└─────────────────────┘                     └─────────────────────┘
```

### Detailed Component Architecture
```
Windows PC Side:                           Raspberry Pi Side:
┌─────────────────────┐                   ┌─────────────────────┐
│  water_gun_client.py│                   │ water_gun_server.py │
│                     │                   │                     │
│  ┌─────────────────┐│                   │┌─────────────────┐  │
│  │ Face Detection  ││                   ││ TCP Server      │  │
│  │ • dlib detector ││                   ││ • JSON Protocol │  │
│  │ • OpenCV KCF    ││                   ││ • Command Handle│  │
│  │ • Bounding box  ││                   │└─────────────────┘  │
│  └─────────────────┘│                   │                     │
│           │          │                   │┌─────────────────┐  │
│  ┌─────────────────┐│    Network        ││ Water Gun       │  │
│  │ Network Client  ││◄─────────────────►││ Controller      │  │
│  │ • TCP Socket    ││   Target coords   ││ • Servo Control │  │
│  │ • Auto-reconnect││   Commands        ││ • Safety Logic  │  │
│  │ • Rate limiting ││                   ││ • Target Lock   │  │
│  └─────────────────┘│                   │└─────────────────┘  │
│           │          │                   │          │          │
│  ┌─────────────────┐│                   │┌─────────────────┐  │
│  │ User Interface  ││                   ││ Hardware GPIO   │  │
│  │ • Live video    ││                   ││ • PWM Control   │  │
│  │ • Targeting UI  ││                   ││ • 3 Servo pins  │  │
│  │ • Status display││                   ││ • Safety checks │  │
│  │ • Key controls  ││                   │└─────────────────┘  │
│  └─────────────────┘│                   └─────────────────────┘
└─────────────────────┘
```

## 🔧 Hardware Architecture

### Physical Setup Diagram
```
                    Water Gun Assembly
                    ┌─────────────────────────────────┐
                    │                                 │
                    │  ┌─────────┐    ┌─────────┐    │
                    │  │ Tilt    │    │ Water   │    │
                    │  │ Servo   │    │ Gun     │    │
                    │  │ (Up/Down│    │         │    │
                    │  └─────────┘    └─────────┘    │
                    │       │              │         │
                    │  ┌─────────┐    ┌─────────┐    │
                    │  │ Pan     │    │ Trigger │    │
                    │  │ Servo   │    │ Servo   │    │
                    │  │(L/Right)│    │ (Fire)  │    │
                    │  └─────────┘    └─────────┘    │
                    │       │              │         │
                    └───────┼──────────────┼─────────┘
                            │              │
                    ┌───────┼──────────────┼─────────┐
                    │       │              │         │
                    │  ┌─────────────────────────┐   │
                    │  │   Raspberry Pi 3B+      │   │
                    │  │                         │   │
                    │  │  GPIO18 ──── Pan Servo  │   │
                    │  │  GPIO19 ──── Tilt Servo │   │
                    │  │  GPIO20 ──── Trigger    │   │
                    │  │  5V/GND ──── Power      │   │
                    │  └─────────────────────────┘   │
                    │                                 │
                    │         Raspberry Pi            │
                    └─────────────────────────────────┘
                                    │
                                    │ WiFi/Ethernet
                                    │
                    ┌─────────────────────────────────┐
                    │                                 │
                    │  ┌─────────────────────────┐   │
                    │  │      Windows PC         │   │
                    │  │                         │   │
                    │  │  ┌─────────────────┐   │   │
                    │  │  │   USB Camera    │   │   │
                    │  │  │   (Face Detect) │   │   │
                    │  │  └─────────────────┘   │   │
                    │  └─────────────────────────┘   │
                    │                                 │
                    │           Control PC            │
                    └─────────────────────────────────┘
```

### Servo Mounting Configuration
```
Side View of Water Gun Mount:

    ┌─────────────────┐ ← Water Gun
    │  ╔═══════════╗  │
    │  ║ Water Gun ║  │
    │  ╚═══════════╝  │
    │        │        │
    │   ┌─────────┐   │ ← Trigger Servo
    │   │ Trigger │   │   (pulls string)
    │   │ Servo   │   │
    │   └─────────┘   │
    └─────────────────┘
           │
    ┌─────────────────┐ ← Tilt Servo
    │   Tilt Servo    │   (up/down)
    │   (Vertical)    │
    └─────────────────┘
           │
    ┌─────────────────┐ ← Pan Servo  
    │   Pan Servo     │   (left/right)
    │  (Horizontal)   │
    └─────────────────┘
           │
    ┌─────────────────┐ ← Base/Mount
    │      Base       │
    └─────────────────┘
```

## 🤖 Recommended Servo Motors

For your small water gun project, here are the best servo options:

### 1. **SG90 Micro Servo** (Recommended for ALL 3 positions)
```
Specifications:
• Size: 22.2 x 11.8 x 31mm
• Weight: 9g
• Torque: 1.8kg/cm (4.8V)
• Speed: 0.1s/60° (4.8V)
• Voltage: 4.8V-6V
• Price: $3-5 each
• Total Cost: $9-15 for 3 servos

Why Perfect for Your Project:
✅ Small and lightweight
✅ Enough torque for small water gun
✅ Standard PWM control
✅ Cheap and widely available
✅ Easy to mount
✅ Low power consumption
```

### 2. **Alternative: MG90S Metal Gear** (If you need more torque)
```
Specifications:
• Size: 22.5 x 12 x 28.5mm
• Weight: 13.4g
• Torque: 2.2kg/cm (4.8V)
• Speed: 0.1s/60° (4.8V)
• Price: $6-8 each

Advantages:
✅ Metal gears (more durable)
✅ Higher torque
✅ Same size as SG90
✅ Better for heavier triggers
```

### 3. **Budget Option: SG92R** (Continuous rotation for special effects)
```
Specifications:
• Continuous rotation servo
• Same size as SG90
• Price: $4-6 each

Use Case:
• Could be used for special rotating effects
• Not recommended for trigger (need position control)
```

## 📊 Servo Specifications Comparison

| Model | Size (mm) | Weight | Torque | Speed | Price | Best For |
|-------|-----------|--------|--------|-------|-------|----------|
| SG90 | 22×12×31 | 9g | 1.8kg/cm | 0.1s/60° | $3-5 | **All positions** |
| MG90S | 23×12×29 | 13g | 2.2kg/cm | 0.1s/60° | $6-8 | Heavy triggers |
| SG92R | 22×12×31 | 9g | 1.8kg/cm | Continuous | $4-6 | Special effects |

## 🔌 Power Requirements

### For 3x SG90 Servos:
```
Power Consumption:
• Idle: ~50mA per servo = 150mA total
• Moving: ~200mA per servo = 600mA total
• Peak (all moving): ~800mA at 5V

Power Supply Options:
1. Raspberry Pi 5V pin (if under 1A total)
2. External 5V 2A power supply (recommended)
3. USB power bank (2A+ capacity)

Wiring:
• All servo red wires → 5V
• All servo brown/black wires → GND
• Signal wires → Individual GPIO pins
```

## 🎯 How the System Works

### Step-by-Step Operation:

1. **Startup**
   ```
   Windows PC: Starts camera and face detection
   Raspberry Pi: Starts server and centers servos
   System: Starts in DISARMED mode (safe)
   ```

2. **Face Detection**
   ```
   Camera captures video frames
   dlib detects faces in each frame
   OpenCV KCF tracker follows detected face
   Coordinates sent to Pi over network
   ```

3. **Servo Tracking**
   ```
   Pi receives target coordinates
   Calculates servo angles for pan/tilt
   Smoothly moves servos to aim at face
   Trigger servo remains in rest position
   ```

4. **Target Lock Sequence** (when ARMED)
   ```
   Face enters center zone (30 pixel tolerance)
   Lock-on timer starts (2 second delay)
   "TARGET LOCKED" appears on screen
   System ready to fire
   ```

5. **Firing Sequence**
   ```
   Trigger servo rotates to pull trigger
   Water gun fires at target
   Trigger servo returns to rest position
   3-second cooldown before next shot
   ```

6. **Safety Systems**
   ```
   Emergency stop available anytime
   Auto-disarm after 5 minutes
   Rate limiting (max 10 shots/minute)
   Manual disarm on program exit
   ```

## 🛠️ Assembly Instructions

### Servo Mounting Order:
1. **Base Mount**: Secure pan servo to stable base
2. **Pan Platform**: Attach platform to pan servo horn
3. **Tilt Mount**: Mount tilt servo on pan platform
4. **Gun Mount**: Attach water gun to tilt servo
5. **Trigger Setup**: Mount trigger servo near trigger
6. **String Connection**: Connect fishing line from trigger servo to gun trigger

### Wiring Diagram:
```
Raspberry Pi GPIO:
┌─────────────────────────────────────┐
│  Pin 2  (5V)     ──── Red wires    │
│  Pin 6  (GND)    ──── Black wires  │
│  Pin 12 (GPIO18) ──── Pan signal   │
│  Pin 35 (GPIO19) ──── Tilt signal  │
│  Pin 38 (GPIO20) ──── Trigger sig  │
└─────────────────────────────────────┘
```

## 🎮 User Experience

### Windows Client Interface:
```
┌─────────────────────────────────────┐
│ Water Gun Tracker Client            │
├─────────────────────────────────────┤
│ [Live Camera Feed with Overlays]    │
│                                     │
│ Status: ARMED/DISARMED              │
│ Pi: Connected/Disconnected          │
│ Target: LOCKED/SEARCHING            │
│                                     │
│ [Firing Zone Rectangle]             │
│ [Crosshair at center]               │
│ [Face tracking rectangle]           │
└─────────────────────────────────────┘

Controls:
A - ARM system    D - DISARM
F - Manual fire   E - Emergency stop
C - Center servos Q - Quit
```

### Raspberry Pi Console Output:
```
🔫 === Water Gun Server ===
🌐 Server: 0.0.0.0:8888
🎯 Pan servo: GPIO18
🎯 Tilt servo: GPIO19  
🔫 Trigger servo: GPIO20
🔫 Water gun controller initialized
📱 Client connected from 192.168.1.100
🎯 TARGET LOCKED
💥 FIRING WATER GUN!
💧 Shot fired! (1/10 this minute)
```

## 🛡️ Safety Features

### Built-in Safety Systems:
- **Default Disarmed**: System starts safe
- **Manual Arming**: Must explicitly arm system
- **Target Lock Delay**: 2-second confirmation
- **Emergency Stop**: Instant disarm (E key)
- **Rate Limiting**: Max 10 shots per minute
- **Auto Timeout**: 5-minute maximum runtime
- **Graceful Shutdown**: Auto-disarms on exit
- **Network Failsafe**: Disarms if connection lost

This system is designed to be fun, safe, and educational while providing a great introduction to computer vision, robotics, and distributed systems!
