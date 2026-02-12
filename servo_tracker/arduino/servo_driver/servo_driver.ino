/*
 * WaterWake Servo Driver — Arduino Uno R3
 *
 * Receives serial commands from Raspberry Pi and drives 3 servos
 * using the hardware-backed Servo library (no jitter).
 *
 * Wiring:
 *   Pin 9  -> Pan servo signal  (horizontal aim)
 *   Pin 10 -> Tilt servo signal (vertical aim)
 *   Pin 11 -> Trigger servo signal
 *   All servo power (red) -> external 5 V supply (NOT the Arduino 5 V pin)
 *   All servo ground (brown/black) -> common GND with Arduino
 *
 * Serial protocol  (9600 baud, newline-terminated):
 *
 *   COMMAND        DESCRIPTION
 *   P<angle>       Set pan angle   (0-180)
 *   T<angle>       Set tilt angle  (0-180)
 *   G<angle>       Set trigger angle directly (0-180)
 *   F              Fire — pull trigger, hold, release
 *   C              Center all servos
 *   S              Report current positions
 *   L<p>,<t>       Set pan AND tilt in one command (less latency)
 *
 * Responses:
 *   OK             Command executed
 *   POS:p,t,g      Current positions  (response to S)
 *   READY          Sent once on boot
 *   ERR:<msg>      Something went wrong
 */

#include <Servo.h>

// --------------- Pin assignments ---------------
static const int PAN_PIN     = 9;
static const int TILT_PIN    = 10;
static const int TRIGGER_PIN = 11;

// --------------- Default angles ----------------
static const int PAN_CENTER     = 90;
static const int TILT_CENTER    = 90;
static const int TRIGGER_REST   = 0;
static const int TRIGGER_FIRE   = 90;

// --------------- Limits ------------------------
static const int ANGLE_MIN = 0;
static const int ANGLE_MAX = 180;

// --------------- Fire timing -------------------
static const unsigned long FIRE_HOLD_MS = 500;

// --------------- Servo objects -----------------
Servo panServo;
Servo tiltServo;
Servo triggerServo;

// --------------- State -------------------------
int currentPan     = PAN_CENTER;
int currentTilt    = TILT_CENTER;
int currentTrigger = TRIGGER_REST;

// --------------- Serial buffer -----------------
static const int BUF_SIZE = 64;
char buf[BUF_SIZE];
int  bufPos = 0;

// -----------------------------------------------
//  Helpers
// -----------------------------------------------

int clampAngle(int angle) {
    if (angle < ANGLE_MIN) return ANGLE_MIN;
    if (angle > ANGLE_MAX) return ANGLE_MAX;
    return angle;
}

void centerAll() {
    currentPan     = PAN_CENTER;
    currentTilt    = TILT_CENTER;
    currentTrigger = TRIGGER_REST;

    panServo.write(PAN_CENTER);
    tiltServo.write(TILT_CENTER);
    triggerServo.write(TRIGGER_REST);
}

void fireTrigger() {
    triggerServo.write(TRIGGER_FIRE);
    currentTrigger = TRIGGER_FIRE;
    delay(FIRE_HOLD_MS);
    triggerServo.write(TRIGGER_REST);
    currentTrigger = TRIGGER_REST;
}

// -----------------------------------------------
//  Command processing
// -----------------------------------------------

void processCommand(const char* cmd, int len) {
    if (len == 0) return;

    char type = cmd[0];
    const char* arg = cmd + 1;   // everything after the first char

    switch (type) {

    case 'P': case 'p': {
        int angle = clampAngle(atoi(arg));
        currentPan = angle;
        panServo.write(angle);
        Serial.println("OK");
        break;
    }

    case 'T': case 't': {
        int angle = clampAngle(atoi(arg));
        currentTilt = angle;
        tiltServo.write(angle);
        Serial.println("OK");
        break;
    }

    case 'G': case 'g': {
        int angle = clampAngle(atoi(arg));
        currentTrigger = angle;
        triggerServo.write(angle);
        Serial.println("OK");
        break;
    }

    case 'L': case 'l': {
        // Combined pan,tilt command: "L90,45"
        int pan = clampAngle(atoi(arg));
        const char* comma = strchr(arg, ',');
        if (comma) {
            int tilt = clampAngle(atoi(comma + 1));
            currentPan  = pan;
            currentTilt = tilt;
            panServo.write(pan);
            tiltServo.write(tilt);
            Serial.println("OK");
        } else {
            Serial.println("ERR:L needs pan,tilt");
        }
        break;
    }

    case 'F': case 'f':
        fireTrigger();
        Serial.println("OK");
        break;

    case 'C': case 'c':
        centerAll();
        Serial.println("OK");
        break;

    case 'S': case 's':
        Serial.print("POS:");
        Serial.print(currentPan);
        Serial.print(',');
        Serial.print(currentTilt);
        Serial.print(',');
        Serial.println(currentTrigger);
        break;

    default:
        Serial.print("ERR:unknown '");
        Serial.print(type);
        Serial.println("'");
        break;
    }
}

// -----------------------------------------------
//  Arduino entry points
// -----------------------------------------------

void setup() {
    Serial.begin(9600);

    panServo.attach(PAN_PIN);
    tiltServo.attach(TILT_PIN);
    triggerServo.attach(TRIGGER_PIN);

    centerAll();

    Serial.println("READY");
}

void loop() {
    while (Serial.available() > 0) {
        char c = (char)Serial.read();

        if (c == '\n' || c == '\r') {
            if (bufPos > 0) {
                buf[bufPos] = '\0';
                processCommand(buf, bufPos);
                bufPos = 0;
            }
        } else if (bufPos < BUF_SIZE - 1) {
            buf[bufPos++] = c;
        }
    }
}
