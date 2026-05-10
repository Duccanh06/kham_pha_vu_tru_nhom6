"""
AI Hand Gesture Controller
Uses MediaPipe Hands to detect:
  - Open hand → Move (index finger tip = direction vector)
  - Fist (closed) → Shoot
  - Peace sign (2 fingers) → Interact
  - Thumbs up → Boost
  - Pinch → Pause/Menu
"""
import threading
import math
import time


class HandController:
    """Thread-safe hand gesture input from camera."""

    GESTURE_NONE      = 'none'
    GESTURE_OPEN      = 'open'       # move
    GESTURE_FIST      = 'fist'       # shoot
    GESTURE_PEACE     = 'peace'      # interact
    GESTURE_THUMBS_UP = 'thumbs_up'  # boost
    GESTURE_PINCH     = 'pinch'      # pause

    def __init__(self):
        self.available = False
        self.running   = False
        self.cap       = None
        self.mp_hands  = None
        self.hands     = None

        # Current state (thread-safe via lock)
        self._lock    = threading.Lock()
        self._gesture = self.GESTURE_NONE
        self._dx      = 0.0   # -1..1 horizontal offset
        self._dy      = 0.0   # -1..1 vertical offset
        self._conf    = 0.0
        self._frame   = None  # latest annotated camera frame
        self._gesture_history = []
        self._last_shoot = 0.0

        self._try_init()

    def _try_init(self):
        try:
            import cv2
            import mediapipe as mp
            self.cv2 = cv2
            self.mp_hands = mp.solutions.hands
            self.mp_draw  = mp.solutions.drawing_utils
            self.mp_styles = mp.solutions.drawing_styles

            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("[HandController] No camera found — hand control disabled")
                return

            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.5,
            )
            self.available = True
            print("[HandController] Camera + MediaPipe ready ✓")
        except Exception as e:
            print(f"[HandController] Init failed: {e}")

    def start(self):
        if not self.available:
            return
        self.running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()

    def _loop(self):
        cv2 = self.cv2
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.03)
                continue

            frame = cv2.flip(frame, 1)
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb)

            gesture = self.GESTURE_NONE
            dx, dy  = 0.0, 0.0
            conf    = 0.0

            if result.multi_hand_landmarks:
                lm = result.multi_hand_landmarks[0]
                # Draw landmarks
                self.mp_draw.draw_landmarks(
                    frame, lm,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_styles.get_default_hand_landmarks_style(),
                    self.mp_styles.get_default_hand_connections_style(),
                )

                gesture, dx, dy, conf = self._classify(lm)

            # Overlay text
            col = (0,255,100) if gesture != self.GESTURE_NONE else (100,100,100)
            cv2.putText(frame, f"Gesture: {gesture}", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
            cv2.putText(frame, f"dx:{dx:+.2f} dy:{dy:+.2f}", (10,60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

            # Box overlay
            h, w = frame.shape[:2]
            cv2.rectangle(frame, (0,0), (w-1,h-1), col, 2)
            cv2.putText(frame, "STELLAR VOID — Hand Control", (10, h-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,200,255), 1)

            with self._lock:
                self._gesture = gesture
                self._dx      = dx
                self._dy      = dy
                self._conf    = conf
                self._frame   = frame.copy()

    def _classify(self, lm):
        """Classify hand gesture from landmarks."""
        pts = [(lm.landmark[i].x, lm.landmark[i].y)
               for i in range(21)]

        # Finger up/down detection
        # Tip indices: Thumb=4, Index=8, Middle=12, Ring=16, Pinky=20
        # Pip indices: 3, 6, 10, 14, 18
        finger_up = [False] * 5

        # Thumb: compare x to PIP (horizontal)
        finger_up[0] = pts[4][0] < pts[3][0]  # left hand mirror

        # Other fingers: tip.y < pip.y
        for i, (tip, pip) in enumerate([(8,6),(12,10),(16,14),(20,18)], start=1):
            finger_up[i] = pts[tip][1] < pts[pip][1]

        n_up = sum(finger_up)

        # Wrist as reference
        wrist = pts[0]
        index_tip = pts[8]

        # Direction: from wrist to index tip (normalized)
        dx = (index_tip[0] - wrist[0]) * 4
        dy = (index_tip[1] - wrist[1]) * 4
        dx = max(-1.0, min(1.0, dx))
        dy = max(-1.0, min(1.0, dy))

        # Pinch detection
        thumb_tip = pts[4]
        dist_pinch = math.hypot(thumb_tip[0]-index_tip[0],
                                 thumb_tip[1]-index_tip[1])

        # Classify
        if dist_pinch < 0.05:
            return self.GESTURE_PINCH, 0, 0, 0.9

        if n_up == 0:
            return self.GESTURE_FIST, dx, dy, 0.9

        if n_up >= 4:
            return self.GESTURE_OPEN, dx, dy, 0.85

        if finger_up[0] and not any(finger_up[1:]):
            return self.GESTURE_THUMBS_UP, dx, dy, 0.8

        if finger_up[1] and finger_up[2] and not finger_up[3] and not finger_up[4]:
            return self.GESTURE_PEACE, dx, dy, 0.85

        return self.GESTURE_NONE, dx, dy, 0.5

    @property
    def gesture(self):
        with self._lock:
            return self._gesture

    @property
    def direction(self):
        with self._lock:
            return self._dx, self._dy

    @property
    def should_shoot(self):
        now = time.time()
        if self.gesture == self.GESTURE_FIST and (now - self._last_shoot) > 0.25:
            self._last_shoot = now
            return True
        return False

    @property
    def frame(self):
        with self._lock:
            return self._frame

    @property
    def is_interacting(self):
        return self.gesture == self.GESTURE_PEACE

    @property
    def is_boosting(self):
        return self.gesture == self.GESTURE_THUMBS_UP
