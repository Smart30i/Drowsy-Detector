import cv2
import numpy as np
import dlib
from imutils import face_utils
import pygame
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# Initialize pygame mixer
pygame.mixer.init()

# Load model
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

cap = cv2.VideoCapture(0)

sleep = drowsy = active = 0
status = ""
color = (0, 0, 0)
current_alarm = None  # Track current playing alarm

# Store EAR values for graph
ear_values = deque(maxlen=100)

# Function to play alarm sound
def play_alarm(alarm_file):
    global current_alarm
    if current_alarm != alarm_file:
        pygame.mixer.music.load(alarm_file)
        pygame.mixer.music.play(-1)
        current_alarm = alarm_file

# Function to stop alarm sound
def stop_alarm():
    global current_alarm
    if current_alarm is not None:
        pygame.mixer.music.stop()
        current_alarm = None

def compute(ptA, ptB):
    return np.linalg.norm(ptA - ptB)

def blinked(a, b, c, d, e, f):
    up = compute(b, d) + compute(c, e)
    down = compute(a, f)
    ratio = up / (2.0 * down)
    
    if ratio > 0.23:
        return 2  # Eyes Open (Active)
    elif 0.20 < ratio <= 0.23:
        return 1  # Drowsy
    else:
        return 0  # Sleeping

# Real-time EAR plot setup
ys = deque([0]*100, maxlen=100)

def start_plot():
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_facecolor('#f0f0f0')
    line, = ax.plot(range(100), ys, lw=2, color='blue')
    ax.set_ylim(0, 0.4)
    ax.set_title("Real-time EAR")
    ax.set_xlabel("Frame")
    ax.set_ylabel("EAR")
    ax.grid(True)
    ax.axhline(y=0.23, color='red', linestyle='--', label='Drowsiness Threshold')
    ax.legend()

    def animate(i):
        if ear_values:
            ys.append(ear_values[-1])
            if len(ys) > 100:
                ys.popleft()
            line.set_ydata(ys)
            line.set_xdata(range(len(ys)))
        return line,

    ani = animation.FuncAnimation(fig, animate, interval=33)
    plt.show()

# Start the graph thread
threading.Thread(target=start_plot, daemon=True).start()

# Main loop
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        landmarks = predictor(gray, face)
        landmarks = face_utils.shape_to_np(landmarks)

        left_blink = blinked(landmarks[36], landmarks[37], 
                             landmarks[38], landmarks[41], 
                             landmarks[40], landmarks[39])
        right_blink = blinked(landmarks[42], landmarks[43], 
                              landmarks[44], landmarks[47], 
                              landmarks[46], landmarks[45])

        # Compute EAR
        left_EAR = (compute(landmarks[37], landmarks[41]) + compute(landmarks[38], landmarks[40])) / (2.0 * compute(landmarks[36], landmarks[39]))
        right_EAR = (compute(landmarks[43], landmarks[47]) + compute(landmarks[44], landmarks[46])) / (2.0 * compute(landmarks[42], landmarks[45]))
        avg_EAR = (left_EAR + right_EAR) / 2.0
        ear_values.append(avg_EAR)

        # Status decision
        if left_blink == 0 or right_blink == 0:
            sleep += 1
            drowsy = active = 0
            if sleep > 6:
                status = "SLEEPING !"
                color = (255, 0, 0)
                threading.Thread(target=play_alarm, args=("Aylex - A Positive Direction (freetouse.com).mp3",), daemon=True).start()

        elif left_blink == 1 or right_blink == 1:
            drowsy += 1
            sleep = active = 0
            if drowsy > 6:
                status = "Drowsy"
                color = (255, 99, 71)
                threading.Thread(target=play_alarm, args=("school-bell-199584.mp3",), daemon=True).start()
        
        else:
            active += 1
            sleep = drowsy = 0
            if active > 6:
                status = "Active ;)"
                color = (255, 165, 0)
                stop_alarm()

        cv2.putText(frame, f"{status}", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        cv2.putText(frame, f"EAR: {avg_EAR:.2f}", (100, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Drowsiness Detector", frame)
    
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()
