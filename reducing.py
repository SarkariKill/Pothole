import cv2 as cv
import time
import geocoder
import os

# Reading label names from obj.names file
class_name = []
with open(os.path.join("project_files", 'obj.names'), 'r') as f:
    class_name = [cname.strip() for cname in f.readlines()]

# Load model weights and config file
net1 = cv.dnn.readNet('project_files/yolov4_tiny.weights', 'project_files/yolov4_tiny.cfg')

# Set backend to CPU since CUDA is not supported
net1.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
net1.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

# Initialize the model with default YOLO input size
model1 = cv.dnn_DetectionModel(net1)
model1.setInputParams(size=(416, 416), scale=1/255, swapRB=True)  # Use YOLO default size

# Use the webcam as video source
cap = cv.VideoCapture(0)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 416)  # Set lower width for performance
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 416)  # Set lower height for performance
width = cap.get(3)
height = cap.get(4)
result = cv.VideoWriter('result.avi', 
                        cv.VideoWriter_fourcc(*'MJPG'), 
                        10, (int(width), int(height)))

# Ensure the result path exists
result_path = "pothole_coordinates"
os.makedirs(result_path, exist_ok=True)

# Initialize parameters
starting_time = time.time()
Conf_threshold = 0.6  # Increased for performance
NMS_threshold = 0.5   # Increased for performance
frame_counter = 0
i, b = 0, 0

# Detection loop
while True:
    ret, frame = cap.read()
    frame_counter += 1
    if not ret:
        break
    
    # Skip frames to reduce load
    if frame_counter % 2 != 0:
        continue
    
    # Detect objects in the frame
    classes, scores, boxes = model1.detect(frame, Conf_threshold, NMS_threshold)
    for (classid, score, box) in zip(classes, scores, boxes):
        label = "pothole"
        x, y, w, h = box
        recarea = w * h
        area = width * height
        
        # Drawing detection boxes for potholes
        if len(scores) != 0 and scores[0] >= 0.7:
            if recarea / area <= 0.1 and box[1] < 600:
                cv.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
                cv.putText(frame, "%" + str(round(scores[0] * 100, 2)) + " " + label, 
                           (box[0], box[1] - 10), cv.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)
                
                # Save detected pothole coordinates and images periodically
                if i == 0 or (time.time() - b) >= 2:
                    g = geocoder.ip('me')  # Update geolocation
                    cv.imwrite(os.path.join(result_path, f'pothole{i}.jpg'), frame)
                    with open(os.path.join(result_path, f'pothole{i}.txt'), 'w') as f:
                        f.write(str(g.latlng))
                    b = time.time()
                    i += 1

    # Display FPS
    endingTime = time.time() - starting_time
    fps = frame_counter / endingTime
    cv.putText(frame, f'FPS: {fps:.2f}', (20, 50), cv.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 0), 2)
    
    # Show frame and save to output video (display every other frame for performance)
    if frame_counter % 2 == 0:
        cv.imshow('frame', frame)
    result.write(frame)
    
    if cv.waitKey(1) == ord('q'):
        break

# Cleanup
cap.release()
result.release()
cv.destroyAllWindows()