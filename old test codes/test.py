import cv2
import numpy as np
import time

# Load the head pose estimation model using OpenVINO
model_xml = "E:\\Github Projs\\WaterWake\\models\\head-pose-estimation-adas-0001.xml"
model_bin = "E:\\Github Projs\\WaterWake\\models\\head-pose-estimation-adas-0001.bin"
net = cv2.dnn.readNet(model_xml, model_bin)

# Initialize variables for the 3-second timer and text display
start_time = None
display_text = False
text_start_time = None

# Function to display text on the frame for a specific duration
def display_text_on_frame(frame, text, duration=3):
    global display_text, text_start_time

    # If display_text is False, don't show the text
    if not display_text:
        return False

    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Check if the display duration is over
    if time.time() - text_start_time >= duration:
        display_text = False
        return False
    return True

# Open the webcam
video_capture = cv2.VideoCapture(0)

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    # Convert the frame to the required input format for OpenVINO
    blob = cv2.dnn.blobFromImage(frame, size=(60, 60), ddepth=cv2.CV_8U)

    # Perform head pose estimation
    net.setInput(blob)
    angles = net.forward()

    # Extract the yaw, pitch, and roll angles from the output
    yaw_angle = angles[0][0]
    pitch_angle = angles[0][1]
    roll_angle = angles[0][2]

    # Determine if the head is facing the side based on yaw angle
    if -45 <= yaw_angle <= 45:
        text = "Facing Forward"
    elif yaw_angle < -45:
        text = "Facing Left"
    else:
        text = "Facing Right"

    # Display the head orientation
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Display the frame with head detection and orientation
    cv2.imshow('Head Detection', frame)

    # Exit the loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and destroy the window
video_capture.release()
cv2.destroyAllWindows()