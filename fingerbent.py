import cv2
from helper import draw_landmarks_on_image, percentage_map, MovingAverageFilter, ThresholdFilter
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
from collections import namedtuple
import numpy as np
from enum import Enum
from collections import deque
import copy
from threading import Thread

Point = namedtuple('Point', ['x', 'y', 'z'])

class FINGERS(Enum):
    THUMB_TOP = 4
    INDEX = 8
    MIDDLE = 12
    RING = 16
    PINKY = 20

def np_point(p):
    return np.array([p.x, p.y, p.z])

def dist(p1, p2=np.array([0,0,0])):
    return np.linalg.norm(p1-p2)

class FingerBent():
    def __init__(self):
        self.cap = cv2.VideoCapture(0)

        # STEP 2: Create an HandLandmarker object.
        base_options = python.BaseOptions(
            model_asset_path='hand_landmarker.task',
        )
        self.options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            running_mode=vision.RunningMode.VIDEO,
            min_hand_detection_confidence=0.3,
            min_hand_presence_confidence=0.3,
            min_tracking_confidence=0.3
        )

        self.val = None

        self.ma_filter = {
            x: MovingAverageFilter(10) for x in FINGERS
        }
        self.th_filter =  {
            x: ThresholdFilter(10) for x in FINGERS
        }

        self.close_values = {}
        self.open_values = {}

    def startThreaded(self):
        self.readthread = Thread(target=self.__readThread).start()

    def __readThread(self):
        current_time = 0
        previous_time = 0
        caliberating_finger = None

        with vision.HandLandmarker.create_from_options(self.options) as detector:
            values = {}
            percentages = None
            mode = 'NORMAL'
            while True:
                success, img = self.cap.read()

                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img)
                ms = self.cap.get(cv2.CAP_PROP_POS_MSEC)
                detection_result = detector.detect_for_video(mp_image, int(ms))

                landmarks = detection_result.__dict__['hand_world_landmarks']
                wrist_pos = []
                index_base_pos = []
                index_tip_pos = []

                test = {}

                if landmarks:
                    wrist = landmarks[0][0]
                    thumbcmc = landmarks[0][1]

                    for finger in FINGERS:
                        tip = landmarks[0][finger.value]
                        dip = landmarks[0][finger.value - 1]
                        pip = landmarks[0][finger.value - 2]
                        mcp = landmarks[0][finger.value - 3]

                        tip2pip = dist(np_point(tip), np_point(pip))
                        tip2mcp = dist(np_point(tip), np_point(mcp))
                        tip2palm = dist(np_point(tip))
                        tip2wrist = dist(np_point(wrist), np_point(tip))
                        tip2tcmc = dist(np_point(tip), np_point(thumbcmc))


                        dip2mcp = dist(np_point(dip), np_point(mcp))
                        dip2palm = dist(np_point(dip))
                        dip2wrist = dist(np_point(wrist), np_point(wrist))
                        dip2tcmc = dist(np_point(dip), np_point(thumbcmc))

                        # These are just values i selected and tested with,
                        # I was in hurry and thse values seemed to work good
                        if finger == FINGERS.THUMB_TOP:
                            value = (0.5*dip2mcp + min(tip2wrist, tip2tcmc) + 2.5*(tip2mcp) + 5.5*(tip2palm + dip2palm)/2 + 0.5*tip2pip)/10.0
                        else:
                            value = (3.5*dip2mcp + 2.5*min(tip2wrist, tip2tcmc) + 2.5*(tip2mcp) + (tip2palm + dip2palm)/2 + 0.5*tip2pip)/10.0
                        values[finger] = round(value,4)

                    if mode == 'NORMAL':
                        if all([
                            (finger in self.close_values and finger in self.open_values) for finger in FINGERS
                        ]):
                            percentages = {}
                            for finger in FINGERS:
                                percentages[finger] = round(
                                    self.th_filter[finger].filter(
                                        self.ma_filter[finger].filter(
                                            100 - percentage_map(self.close_values[finger], self.open_values[finger], values[finger])
                                        )
                                    ),
                                    2
                                )
                        else:
                            percentages = None


                current_time = time.time()
                fps = 1/(current_time - previous_time)
                previous_time = current_time

                self.val = percentages


                annotated_image = draw_landmarks_on_image(mp_image.numpy_view(), detection_result)
                annotated_image = cv2.resize(annotated_image, (800,600))

                if mode == 'NORMAL':
                    cv2.putText(annotated_image, f"{[x.name for x in values.keys()]}", (10,50), cv2.FONT_HERSHEY_PLAIN, 1,(255,0,0))
                    cv2.putText(annotated_image, f"{list(values.values())}", (10,70), cv2.FONT_HERSHEY_PLAIN, 1,(255,0,0))
                    if percentages:
                        cv2.putText(annotated_image, f"{list(percentages.values())}", (10,100), cv2.FONT_HERSHEY_PLAIN, 1,(255,0,0))
                    else:
                        cv2.putText(annotated_image, "All figners not caliberated", (10, 100), cv2.FONT_HERSHEY_PLAIN, 1, (255,0,0))
                else:
                    cv2.putText(annotated_image, f"CALIBERATING, {caliberating_finger.name}", (10,50), cv2.FONT_HERSHEY_PLAIN, 1,(255,0,0))
                    cv2.putText(annotated_image, f"Press 'o'/'c' to capture open/close value", (10,70), cv2.FONT_HERSHEY_PLAIN, 1,(255,0,0))
                    cv2.putText(annotated_image, f"Press n to goto normal mode", (10,100), cv2.FONT_HERSHEY_PLAIN, 1,(255,0,0))


                cv2.imshow("FINGER BENT", annotated_image)
                key = cv2.waitKey(10)

                if key >= ord('0') and key <= ord('4'):
                    caliberating_finger = FINGERS([x.value for x in FINGERS][key - ord('0')])
                    mode = 'CALIB'
                elif key == ord('n'):
                    mode = 'NORMAL'
                elif key in [ord('o'), ord('c')] and mode == 'CALIB':
                    working_value = {ord('o'):self.open_values, ord('c'):self.close_values}[key]
                    if values.get(caliberating_finger, None):
                        working_value[caliberating_finger] = values[caliberating_finger]


if __name__ == "__main__":
    webcam = FingerBent()
    webcam.startThreaded()
