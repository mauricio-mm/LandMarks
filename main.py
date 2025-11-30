import sys
import cv2
import mediapipe as mp
import numpy as np
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(
    min_detection_confidence=0.7,   
    min_tracking_confidence=0.7,  
    model_complexity=2,            
    smooth_landmarks=True          
)

class AppMP(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("interface.ui", self)
        
        self.cap = None
        self.timer = None
        self.camera_on = False
        self.exercise_started = False
        
        self.selected_exercise = 0 
        self.target_reps = 0
        self.rep_counter = 0
        self.exercise_state = None

        self.lcdNumber_2.display(self.target_reps)

        self.pushButton.clicked.connect(self.increment_lcd2)
        self.pushButton_2.clicked.connect(self.decrement_lcd2)

        self.btn_start_camera.clicked.connect(self.toggle_camera)
        self.btn_start_exercise.clicked.connect(self.toggle_exercise)
        self.btn_start_exercise.setEnabled(False)

    def toggle_camera(self):
        if not self.camera_on:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                QMessageBox.critical(self, "Camera Error", "Unable to open the camera.")
                return
            
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(30)

            self.btn_start_camera.setText("OFF")
            self.btn_start_camera.setStyleSheet("background-color: rgb(200, 50, 50); color: white;")
            self.camera_on = True
            
            self.btn_start_exercise.setEnabled(True)
        else:
            if self.timer:
                self.timer.stop()
            if self.cap:
                self.cap.release()
            
            self.camera_feed.clear()
            self.camera_feed.setText("OFF")
            self.btn_start_camera.setText("ON")
            self.btn_start_camera.setStyleSheet("")
            self.camera_on = False
            
            if self.exercise_started:
                self.toggle_exercise()
                
            self.btn_start_exercise.setEnabled(False)

    def toggle_exercise(self):
        if not self.camera_on:
            QMessageBox.critical(self, "Error", "Turn on the camera before starting the exercise.")
            return

        if not self.exercise_started:

            if self.radio_ex1.isChecked():
                self.selected_exercise = 1  
            elif self.radio_ex2.isChecked():
                self.selected_exercise = 2  
            elif self.radio_ex3.isChecked():
                self.selected_exercise = 3  
            elif self.radio_ex4.isChecked():
                self.selected_exercise = 4  

            self.rep_counter = 0
           
            if self.selected_exercise == 3:
                self.exercise_state = "down"
            else:
                self.exercise_state = "lowering"
            
            self.exercise_started = True
            self.btn_start_exercise.setText("STOP")
            self.btn_start_exercise.setStyleSheet("background-color: rgb(200, 0, 0); color: #fefefe;")
            self.verticalLayout_2.setEnabled(False)
       
        else:
            self.exercise_started = False
            self.btn_start_exercise.setText("START")
            self.btn_start_exercise.setStyleSheet("background-color: #0077AA; color: #fefefe;")
            self.group_exercicios.setEnabled(True)
            self.verticalLayout_2.setEnabled(True)

            QMessageBox.information(self, "Status", "Exercise completed")

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
            
        frame = cv2.resize(frame, (self.camera_feed.width(), self.camera_feed.height()))
        frame = cv2.flip(frame, 1)
        
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        result = pose.process(image_rgb)
        image_rgb.flags.writeable = True
        processed_frame = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        try:
            if self.exercise_started and result.pose_landmarks:
                landmarks = result.pose_landmarks.landmark
                
                # JUMPING JACK
                if self.selected_exercise == 1:
                    hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                    
                    angle = self.calculate_angle(hip, shoulder, wrist)

                    if angle < 40 and self.exercise_state == "raising":
                        self.exercise_state = "lowering"
                    if angle > 140 and self.exercise_state == "lowering":
                        self.exercise_state = "raising"
                        self.rep_counter += 1

                # SQUAT
                elif self.selected_exercise == 2:
                    hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                    ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]

                    angle = self.calculate_angle(hip, knee, ankle)

                    if angle > 170 and self.exercise_state == "raising":
                        self.exercise_state = "lowering"
                    if angle < 90 and self.exercise_state == "lowering":
                        self.exercise_state = "raising"
                        self.rep_counter += 1

                # ABDOMINAL
                elif self.selected_exercise == 3:
                    shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]

                    angle = self.calculate_angle(shoulder, hip, knee)

                    if angle > 150 and self.exercise_state == "raising":
                        self.exercise_state = "down"
                    if angle < 90 and self.exercise_state == "down":
                        self.exercise_state = "raising"
                        self.rep_counter += 1

                # BICEP CURL
                elif self.selected_exercise == 4:
                    shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                    wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                    
                    angle = self.calculate_angle(shoulder, elbow, wrist)
                    
                    if angle > 160 and self.exercise_state == "raising":
                        self.exercise_state = "lowering"
                    if angle < 40 and self.exercise_state == "lowering":
                        self.exercise_state = "raising"
                        self.rep_counter += 1

        except:
            pass

        if result.pose_landmarks:
            mp_drawing.draw_landmarks(
                processed_frame, 
                result.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS
            )

        if self.exercise_started:
            self.lcdNumber.display(self.rep_counter)

            if self.rep_counter >= self.target_reps:
                self.toggle_exercise()

        self.display_frame_on_screen(processed_frame)

    def display_frame_on_screen(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.camera_feed.setPixmap(QPixmap.fromImage(img))

    def closeEvent(self, event):
        if self.timer:
            self.timer.stop()
        if self.cap:
            self.cap.release()
        
        pose.close() 
        event.accept()
    
    def increment_lcd2(self):
        self.target_reps += 1
        self.lcdNumber_2.display(self.target_reps)

    def decrement_lcd2(self):
        if self.target_reps > 0:
            self.target_reps -= 1
        self.lcdNumber_2.display(self.target_reps)

    def calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle

        return angle
    

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = AppMP()
    window.show()
    sys.exit(app.exec_())
