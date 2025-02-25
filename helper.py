from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import numpy as np
import cv2
import numpy as np
from collections import deque

class MovingAverageFilter:
    def __init__(self, window_size):
        self.window_size = window_size
        self.data_window = deque(maxlen=window_size)
        self.sum = 0.0

    def filter(self, new_value):
        if len(self.data_window) == self.window_size:
            self.sum -= self.data_window[0]
        self.data_window.append(new_value)
        self.sum += new_value
        return self.sum / len(self.data_window)

class ThresholdFilter:
    def __init__(self, threshold):
        """
        Initialize the ThresholdFilter.
        :param threshold: Minimum absolute change required to accept a new value.
        """
        self.threshold = threshold
        self.prev_value = None  # To store the last accepted value

    def filter(self, new_value):
        """
        Apply the threshold filter on the new value.
        :param new_value: The latest value from the data stream.
        :return: The filtered value.
        """
        if self.prev_value is None:
            # First value initializes the filter
            self.prev_value = new_value
        elif abs(new_value - self.prev_value) >= self.threshold:
            # Update only if the change exceeds the threshold
            self.prev_value = new_value

        return self.prev_value

def percentage_map(xmin, xmax, x):
    omax = 100
    omin = 0
    x = max(xmin, x)
    x = min(xmax, x)
    slope = 1.0 * (omax - omin) / (xmax - xmin)
    output = omin + slope * (x - xmin)
    return output


MARGIN = 10  # pixels
FONT_SIZE = 1
FONT_THICKNESS = 1
HANDEDNESS_TEXT_COLOR = (88, 205, 54) # vibrant green

def draw_landmarks_on_image(rgb_image, detection_result):
  hand_landmarks_list = detection_result.hand_landmarks
  handedness_list = detection_result.handedness
  annotated_image = np.copy(rgb_image)

  # Loop through the detected hands to visualize.
  for idx in range(len(hand_landmarks_list)):
    hand_landmarks = hand_landmarks_list[idx]
    handedness = handedness_list[idx]

    # Draw the hand landmarks.
    hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
    hand_landmarks_proto.landmark.extend([
      landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
    ])
    solutions.drawing_utils.draw_landmarks(
      annotated_image,
      hand_landmarks_proto,
      solutions.hands.HAND_CONNECTIONS,
      solutions.drawing_styles.get_default_hand_landmarks_style(),
      solutions.drawing_styles.get_default_hand_connections_style())

    # Get the top left corner of the detected hand's bounding box.
    height, width, _ = annotated_image.shape
    x_coordinates = [landmark.x for landmark in hand_landmarks]
    y_coordinates = [landmark.y for landmark in hand_landmarks]
    text_x = int(min(x_coordinates) * width)
    text_y = int(min(y_coordinates) * height) - MARGIN

    # Draw handedness (left or right hand) on the image.
    cv2.putText(annotated_image, f"{handedness[0].category_name}",
                (text_x, text_y), cv2.FONT_HERSHEY_PLAIN,
                FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)

  return annotated_image
