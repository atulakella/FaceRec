import face_recognition
import os
import sys
import cv2
import numpy as np
import math
import time

def face_confidence(face_distance, face_match_threshold=0.6):
    range_val = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range_val * 2.0)
    
    if face_distance > face_match_threshold:
        return str(round(linear_val * 100, 2)) + '%'
    else:
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2)) + '%'

class FaceRecognition:
    face_locations = []
    face_encodings = []
    face_names = []
    known_face_encodings = []
    known_face_names = []
    process_current_frame = True

    smoothing_factor = 0.2  # Adjust this value for more or less smoothing

    def __init__(self):
        self.encode_faces()
    
    def encode_faces(self):
        for image in os.listdir('face'):
            face_image = face_recognition.load_image_file(f'face/{image}')
        
            try:
                face_encoding = face_recognition.face_encodings(face_image)[0]
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(image)
            except IndexError:
                print(f"No face found in {image}. Skipping...")

        print(self.known_face_names)

    def run_recognition(self):
        # Specify the index of the external USB webcam (adjust if needed)
        video_capture = cv2.VideoCapture(0)

        # Check if the video capture is successful
        if not video_capture.isOpened():
            print('Error: Unable to open video source.')
            sys.exit()

        # Allow the camera to warm up
        cv2.waitKey(1000)

        smoothed_face_locations = []

        # Variables for FPS calculation
        start_time = time.time()
        frame_count = 0

        while True:
            ret, frame = video_capture.read()

            # Check if the frame is captured successfully
            if not ret:
                print('Error: Unable to capture frame.')
                break

            # Calculate FPS
            frame_count += 1
            elapsed_time = time.time() - start_time
            fps = frame_count / elapsed_time

            # Overlay FPS on the frame
            cv2.putText(frame, f'FPS: {round(fps, 2)}', (frame.shape[1] - 100, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            if self.process_current_frame:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = small_frame[:, :, ::-1]

                self.face_locations = face_recognition.face_locations(rgb_small_frame)
                self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)

                self.face_names = []
                for face_encoding in self.face_encodings:
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    name = 'Unknown'
                    confidence = 'Unknown'

                    face_distance = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distance)

                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
                        confidence = face_confidence(face_distance[best_match_index])
                    self.face_names.append(f'{name}({confidence})')

                # Smooth the face locations using a simple moving average
                if smoothed_face_locations:
                    for i in range(len(self.face_locations)):
                        smoothed_face_locations[i] = (
                            int(self.smoothing_factor * self.face_locations[i][0] + (1 - self.smoothing_factor) * smoothed_face_locations[i][0]),
                            int(self.smoothing_factor * self.face_locations[i][1] + (1 - self.smoothing_factor) * smoothed_face_locations[i][1]),
                            int(self.smoothing_factor * self.face_locations[i][2] + (1 - self.smoothing_factor) * smoothed_face_locations[i][2]),
                            int(self.smoothing_factor * self.face_locations[i][3] + (1 - self.smoothing_factor) * smoothed_face_locations[i][3])
                        )
                else:
                    smoothed_face_locations = self.face_locations

            self.process_current_frame = not self.process_current_frame

            for (top, right, bottom, left), name in zip(smoothed_face_locations, self.face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 225), 2)
                cv2.rectangle(frame, (left, bottom-35), (right, bottom), (0, 0, 225), -1)
                cv2.putText(frame, name, (left+6, bottom-6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
            
            cv2.imshow('Face Recognition', frame)

            if cv2.waitKey(1) == ord('q'):
                break
        
        video_capture.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    fr = FaceRecognition()
    fr.run_recognition()
