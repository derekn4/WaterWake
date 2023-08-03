import cv2
import dlib

# Load face detector from dlib
face_detector = dlib.get_frontal_face_detector()

# Open the webcam
video_capture = cv2.VideoCapture(0)

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    # Convert the frame to grayscale for faster processing
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the grayscale frame
    faces = face_detector(gray)

    for face in faces:
        # Get the head region from the frame
        (startX, startY, endX, endY) = (face.left(), face.top(), face.right(), face.bottom())
        
        # Expand the size of the bounding box
        padding = 30  # Adjust this value as needed
        startX -= padding
        startY -= padding
        endX += padding
        endY += padding

        # Make sure the bounding box stays within the frame boundaries
        startX = max(0, startX)
        startY = max(0, startY)
        endX = min(frame.shape[1], endX)
        endY = min(frame.shape[0], endY)
        
        head = frame[startY:endY, startX:endX]

        # Draw a rectangle around the detected head
        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)

    # Display the frame with head detection
    cv2.imshow('Head Detection', frame)

    # Exit the loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and destroy the window
video_capture.release()
cv2.destroyAllWindows()