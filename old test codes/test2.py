import cv2
import time

# Load face detector from OpenCV
face_cascade = cv2.CascadeClassifier('E:\\Github Projs\\WaterWake\\models\\haarcascade_frontalface_default.xml')
left_ear_cascade = cv2.CascadeClassifier('E:\\Github Projs\\WaterWake\\models\\haarcascade_mcs_leftear.xml')
right_ear_cascade = cv2.CascadeClassifier('E:\\Github Projs\\WaterWake\\models\\haarcascade_mcs_rightear.xml')

# Create a background subtractor object
bg_subtractor = cv2.createBackgroundSubtractorMOG2()

# Open the webcam
video_capture = cv2.VideoCapture(0)

no_detection_time = 0
quit_timeout = 10  # Time in seconds

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    # Apply background subtraction
    fg_mask = bg_subtractor.apply(frame)
    
    # Convert the frame to grayscale for faster processing
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Combine background-subtracted frame with grayscale frame
    filtered_frame = cv2.bitwise_and(gray, gray, mask=fg_mask)

    # Detect faces in the grayscale frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) > 0:
        # Reset no_detection_time if a face is detected
        no_detection_time = 0

        for (x, y, w, h) in faces:
            # Draw a bounding box around the detected face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    else:
        # Increment no_detection_time if no face is detected
        no_detection_time += 1

        # Detect left ears in the grayscale frame
        left_ears = left_ear_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Detect right ears in the grayscale frame
        right_ears = right_ear_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw bounding boxes around ears if detected
        for (ex, ey, ew, eh) in left_ears:
            cv2.rectangle(frame, (ex, ey), (ex + ew, ey + eh), (0, 255, 255), 2)

        for (ex, ey, ew, eh) in right_ears:
            cv2.rectangle(frame, (ex, ey), (ex + ew, ey + eh), (0, 255, 255), 2)

    # Display the frame with either face or ear detection
    cv2.imshow('Face and Ear Detection', frame)

    # Exit the loop if 'q' key is pressed or if no_detection_time exceeds quit_timeout
    if cv2.waitKey(1) & 0xFF == ord('q') or no_detection_time >= quit_timeout * 30:
        break

# Release the webcam and destroy the window
video_capture.release()
cv2.destroyAllWindows()