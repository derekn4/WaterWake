# Water Gun Trigger Control Guide

This guide explains how to add trigger control to your servo head tracker to create a water gun alarm system.

## 🎯 Project Overview

You'll need to add a third actuator to pull the water gun trigger when a face is detected and tracked. Here are several mechanical approaches:

## 🔧 Mechanical Solutions

### Option 1: Servo-Powered Trigger Pull (Recommended)
**Components Needed:**
- 1x Additional servo motor (SG90 or similar)
- 3D printed or fabricated trigger arm
- Small zip ties or wire
- Mounting bracket

**How it Works:**
```
Servo → Arm → String/Wire → Trigger
```

**Advantages:**
- Precise control over trigger pull
- Can control pull strength
- Easy to integrate with existing code
- Reliable and repeatable

**Implementation:**
1. Mount a servo near the trigger guard
2. Attach a lever arm to the servo horn
3. Connect the arm to the trigger with fishing line or thin wire
4. Program servo to rotate and pull trigger when target is centered

### Option 2: Solenoid Actuator
**Components Needed:**
- 12V push/pull solenoid
- Relay module for Pi control
- 12V power supply
- Mounting bracket
- Connecting rod

**How it Works:**
```
Pi GPIO → Relay → Solenoid → Rod → Trigger
```

**Advantages:**
- Very fast trigger pull
- Strong force
- Simple on/off control

**Disadvantages:**
- Requires additional power supply
- Less precise control
- More complex wiring

### Option 3: Linear Actuator (Mini)
**Components Needed:**
- Small linear actuator (12V)
- Motor driver (L298N)
- Mounting hardware
- Connecting rod

**Advantages:**
- Very precise positioning
- Strong force
- Can control extension distance

**Disadvantages:**
- More expensive
- Requires motor driver
- Slower than servo

## 🛠️ Recommended Implementation (Servo Method)

### Hardware Setup

#### Additional Components:
- **Servo**: SG90 micro servo ($3-5)
- **Trigger Arm**: 3D printed or bent wire
- **Connection**: Fishing line or thin steel wire
- **Mounting**: Small bracket or zip ties

#### Wiring:
```
Trigger Servo:
- Signal → GPIO 20 (or available pin)
- Power  → 5V
- Ground → GND
```

#### Mechanical Assembly:
1. **Mount the servo** near the water gun trigger
2. **Create trigger arm** - bend a paperclip or 3D print a small lever
3. **Attach to servo horn** with small screw or zip tie
4. **Connect to trigger** with fishing line or thin wire
5. **Test range of motion** to ensure proper trigger pull

### Software Implementation

I'll create an enhanced version that includes trigger control:

#### GPIO Pin Assignment:
- GPIO 18: Pan servo
- GPIO 19: Tilt servo  
- GPIO 20: Trigger servo

#### Trigger Logic:
- Pull trigger when face is centered and tracked for 2+ seconds
- Release trigger after 0.5 seconds
- Cooldown period of 3 seconds between shots

## 🎮 Enhanced Control Features

### Trigger Modes:
1. **Auto Mode**: Fires when target is centered
2. **Manual Mode**: Fire on command (spacebar)
3. **Burst Mode**: Multiple shots
4. **Safety Mode**: Trigger disabled

### Targeting Logic:
- Only fire when face is within center deadzone
- Require minimum tracking confidence
- Implement "lock-on" delay to avoid accidental firing

## 🔧 3D Printable Parts

### Trigger Arm Design:
```
Simple L-shaped arm:
- 30mm long arm
- 10mm wide
- Servo horn mounting hole
- Wire attachment point
```

### Servo Mount:
```
Clamp-style mount:
- Fits around water gun barrel/body
- Servo mounting holes
- Adjustable position
```

## ⚡ Alternative Quick Solutions

### Option A: Rubber Band Method
- Attach rubber band to trigger
- Use servo to pull rubber band
- Simple but less reliable

### Option B: Cam Mechanism
- Servo rotates a cam
- Cam pushes against trigger
- Good for consistent trigger pull

### Option C: Gear Reduction
- Use servo with gear reduction
- More torque for heavy triggers
- Slower but more powerful

## 🛡️ Safety Considerations

### Important Safety Features:
1. **Manual Override**: Physical switch to disable trigger
2. **Timeout**: Automatic shutdown after X minutes
3. **Low Water Detection**: Stop firing when empty
4. **Emergency Stop**: Big red button to stop everything
5. **Safe Mode**: Default to trigger disabled on startup

### Recommended Safety Code:
```python
# Safety timeouts
MAX_CONTINUOUS_RUNTIME = 300  # 5 minutes
TRIGGER_COOLDOWN = 3.0        # 3 seconds between shots
MAX_SHOTS_PER_MINUTE = 10     # Rate limiting

# Safety checks
def is_safe_to_fire():
    return (
        system_armed and
        not emergency_stop and
        time_since_last_shot > TRIGGER_COOLDOWN and
        shots_this_minute < MAX_SHOTS_PER_MINUTE
    )
```

## 🎯 Targeting Accuracy

### Center Deadzone:
```python
# Only fire when target is very close to center
CENTER_TOLERANCE = 30  # pixels from center
frame_center_x = frame_width // 2
frame_center_y = frame_height // 2

target_centered = (
    abs(target_x - frame_center_x) < CENTER_TOLERANCE and
    abs(target_y - frame_center_y) < CENTER_TOLERANCE
)
```

### Lock-on Delay:
```python
# Require target to be centered for 2 seconds before firing
LOCK_ON_TIME = 2.0
if target_centered:
    lock_on_timer += dt
    if lock_on_timer > LOCK_ON_TIME:
        fire_trigger()
else:
    lock_on_timer = 0
```

## 🔌 Power Considerations

### Power Requirements:
- **3 Servos**: ~1.5A peak (SG90 servos)
- **Pi**: ~0.5A
- **Total**: ~2A at 5V

### Power Solutions:
1. **USB Power Bank**: 2A+ capacity
2. **Wall Adapter**: 5V 3A supply
3. **Separate Servo Power**: Dedicated 5V supply for servos

## 🧪 Testing Procedure

### Step-by-Step Testing:
1. **Test trigger servo alone** - verify range of motion
2. **Test trigger pull** - ensure it actually fires the gun
3. **Test with tracking** - verify targeting accuracy
4. **Test safety features** - emergency stop, timeouts
5. **Test full system** - end-to-end functionality

### Calibration:
1. **Trigger Pull Distance**: Adjust servo angle for proper trigger pull
2. **Trigger Release**: Ensure trigger fully releases
3. **Center Deadzone**: Tune targeting tolerance
4. **Lock-on Time**: Adjust delay before firing

## 📦 Shopping List

### Essential Components:
- [ ] SG90 Micro Servo ($3-5)
- [ ] Jumper wires ($2)
- [ ] Fishing line or thin wire ($2)
- [ ] Small zip ties ($2)
- [ ] Mounting hardware ($3)

### Optional Upgrades:
- [ ] Emergency stop button ($5)
- [ ] LED indicators ($3)
- [ ] Buzzer for audio feedback ($2)
- [ ] Water level sensor ($5)

### Tools Needed:
- [ ] Screwdriver
- [ ] Wire strippers
- [ ] Hot glue gun (for mounting)
- [ ] Drill (if making custom mounts)

## 🎨 Fun Enhancements

### Visual Feedback:
- LED that lights up when target is locked
- Different colors for different modes
- Laser pointer for aiming (optional)

### Audio Feedback:
- Beep when target acquired
- Warning sound before firing
- Voice announcements

### Advanced Features:
- Multiple target tracking
- Face recognition (only fire at specific people)
- Time-based activation (alarm clock mode)
- Remote control via smartphone

This water gun alarm will be an awesome project! The servo-based trigger mechanism is the most reliable and easiest to implement with your existing setup.
