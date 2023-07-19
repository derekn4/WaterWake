import cv2
import dlib
from imutils import face_utils

# Load face detector from dlib
face_detector = dlib.get_frontal_face_detector()
eye_detector = dlib.shape_predictor('C:\\Users\\Derek\\Desktop\\Random Projs\\facial\\models\\shape_predictor_68_face_landmarks.dat')

# Initialize variables for eye aspect ratio (EAR) calculation
EYE_AR_THRESH = 0.3
EYE_AR_CONSEC_FRAMES = 3
frame_counter = 0

def eye_aspect_ratio(eye):
    # Compute the euclidean distances between the two sets of vertical eye landmarks (x, y)-coordinates
    A = euclidean_distance(eye[1], eye[5])
    B = euclidean_distance(eye[2], eye[4])

    # Compute the euclidean distance between the horizontal eye landmark (x, y)-coordinates
    C = euclidean_distance(eye[0], eye[3])

    # Compute the eye aspect ratio
    ear = (A + B) / (2.0 * C)

    return ear

def euclidean_distance(a, b):
    # Compute and return the euclidean distance between two points
    return ((a[0] - b[0])**2 + (a[1] - b[1])**2)**0.5


# Open the webcam
video_capture = cv2.VideoCapture(1)

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
        head = frame[startY:endY, startX:endX]

        # Draw a rectangle around the detected head
        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
        
        # Determine the facial landmarks for the face region
        shape = eye_detector(gray, face)
        shape = face_utils.shape_to_np(shape)

        # Extract the left and right eye coordinates
        left_eye = shape[36:42]
        right_eye = shape[42:48]

        # Compute the eye aspect ratio (EAR) for both eyes
        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)

        # Compute the average EAR
        ear = (left_ear + right_ear) / 2.0

        # Draw the eyes' contours on the frame
        left_eye_hull = cv2.convexHull(left_eye)
        right_eye_hull = cv2.convexHull(right_eye)
        cv2.drawContours(frame, [left_eye_hull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [right_eye_hull], -1, (0, 255, 0), 1)


    # Display the frame with head detection
    cv2.imshow('Head Detection', frame)

    # Exit the loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and destroy the window
video_capture.release()
cv2.destroyAllWindows()