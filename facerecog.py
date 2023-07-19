import cv2
import numpy as np


print(cv2.__file__)
webcam_index = 1  # Use 0 for the first webcam, 1 for the second, and so on

# Create an instance of VideoCapture with the webcam index
video_capture = cv2.VideoCapture(webcam_index)

# Check if the webcam was successfully opened
if not video_capture.isOpened():
    print("Failed to open the webcam. Make sure it is connected and try again.")
    exit()

face_cascade = cv2.CascadeClassifier('C:\\Users\\Derek\\Desktop\\Random Projs\\facial\\models\\haarcascade_frontalface_default.xml')
#right_eye_cascade = cv2.CascadeClassifier('C:\\Users\\Derek\\Desktop\\Random Projs\\facial\\haarcascade_mcs_righteye.xml')
#left_eye_cascade = cv2.CascadeClassifier('C:\\Users\\Derek\\Desktop\\Random Projs\\facial\\haarcascade_mcs_lefteye.xml')

stop_flag = False
# Global variables for width and height
width = 0
height = 0

def on_button_click(event, x, y, flags, param):
    global stop_flag
    if event == cv2.EVENT_LBUTTONDOWN:
        if x > width - 100 and y > height - 50:
            stop_flag = True

cv2.namedWindow('Face and Eye Detection')
cv2.setMouseCallback('Face and Eye Detection', on_button_click)

def perform_face_recognition():
    global width, height
    confidence_threshold = 0.8
    while True:
        # Capture frame-by-frame from the webcam
        ret, frame = video_capture.read()

        # Convert the frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Perform face detection
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around the detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            label = "Face"
            cv2.putText(frame, label, (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Region of Interest (ROI) for the face
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]

            # Perform eye detection within the face region
            #right_eyes = right_eye_cascade.detectMultiScale(roi_gray)
            #left_eyes = left_eye_cascade.detectMultiScale(roi_gray)
            
            #for (ex, ey, ew, eh) in right_eyes:
                # Draw a rectangle around the right eye
            #    cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (255, 0, 0), 2)

            #for (ex, ey, ew, eh) in left_eyes:
                # Draw a rectangle around the left eye
            #    cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (255, 0, 0), 2)

        # Get the dimensions of the frame
        height, width = frame.shape[:2]

        # Add the button rectangle
        button_rect = (width - 100, height - 50, 80, 30)
        cv2.rectangle(frame, button_rect[:2], (button_rect[0] + button_rect[2], button_rect[1] + button_rect[3]), (0, 0, 255), -1)

        # Add the button label
        button_label = "Stop"
        cv2.putText(frame, button_label, (width - 85, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Display the resulting frame with face detection
        cv2.imshow('Face and Eye Detection', frame)


        # Exit the loop if 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q') or stop_flag:
            break

    # Release the webcam and destroy the window
    video_capture.release()
    cv2.destroyAllWindows()

perform_face_recognition()