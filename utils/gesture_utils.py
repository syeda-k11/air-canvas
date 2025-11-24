import mediapipe as mp
import numpy as np

class GestureRecognizer:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255), # Cyan
        ]
        self.current_color_index = 0
    
    def is_drawing_gesture(self, results, img_h, img_w):
        if results.multi_hand_landmarks:
            landmarks = results.multi_hand_landmarks[0].landmark
            index_tip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            index_pip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
            
            # Check if index finger is extended and others are folded
            return (index_tip.y < index_pip.y and 
                    landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y > 
                    landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y)
        return False
    
    def is_eraser_gesture(self, results, img_h, img_w):
        if results.multi_hand_landmarks:
            landmarks = results.multi_hand_landmarks[0].landmark
            thumb_tip = landmarks[self.mp_hands.HandLandmark.THUMB_TIP]
            index_tip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            
            # Check for pinch gesture (thumb and index finger close)
            distance = np.sqrt((thumb_tip.x - index_tip.x)**2 + 
                              (thumb_tip.y - index_tip.y)**2)
            return distance < 0.05
        return False
    
    def is_clear_canvas_gesture(self, results, img_h, img_w):
        if results.multi_hand_landmarks:
            landmarks = results.multi_hand_landmarks[0].landmark
            # Check if all fingers are extended (open palm)
            return all(
                landmarks[tip].y < landmarks[pip].y
                for tip, pip in [
                    (self.mp_hands.HandLandmark.THUMB_TIP, self.mp_hands.HandLandmark.THUMB_IP),
                    (self.mp_hands.HandLandmark.INDEX_FINGER_TIP, self.mp_hands.HandLandmark.INDEX_FINGER_PIP),
                    (self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP, self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP),
                    (self.mp_hands.HandLandmark.RING_FINGER_TIP, self.mp_hands.HandLandmark.RING_FINGER_PIP),
                    (self.mp_hands.HandLandmark.PINKY_TIP, self.mp_hands.HandLandmark.PINKY_PIP)
                ]
            )
        return False
    
    def get_color_change_gesture(self, results, img_h, img_w):
        if results.multi_hand_landmarks:
            landmarks = results.multi_hand_landmarks[0].landmark
            thumb_tip = landmarks[self.mp_hands.HandLandmark.THUMB_TIP]
            pinky_tip = landmarks[self.mp_hands.HandLandmark.PINKY_TIP]
            
            # Check for thumb and pinky extended (like a phone gesture)
            thumb_extended = thumb_tip.y < landmarks[self.mp_hands.HandLandmark.THUMB_IP].y
            pinky_extended = pinky_tip.y < landmarks[self.mp_hands.HandLandmark.PINKY_PIP].y
            others_folded = all(
                landmarks[tip].y > landmarks[pip].y
                for tip, pip in [
                    (self.mp_hands.HandLandmark.INDEX_FINGER_TIP, self.mp_hands.HandLandmark.INDEX_FINGER_PIP),
                    (self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP, self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP),
                    (self.mp_hands.HandLandmark.RING_FINGER_TIP, self.mp_hands.HandLandmark.RING_FINGER_PIP)
                ]
            )
            
            if thumb_extended and pinky_extended and others_folded:
                self.current_color_index = (self.current_color_index + 1) % len(self.colors)
                return self.colors[self.current_color_index]
        return None