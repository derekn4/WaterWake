import cv2

backends = cv2.dnn.availableBackends()
print("Available DNN backends:", backends)