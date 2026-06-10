import base64
import math
import os
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List

import cv2
import numpy as np
from django.conf import settings

HAAR_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Returns distance in meters
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def decode_base64_image(data_url: str) -> np.ndarray:
    # data_url like: data:image/jpeg;base64,/9j/4AAQ...
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    img_bytes = base64.b64decode(data_url)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def detect_face(gray: np.ndarray) -> Optional[np.ndarray]:
    face_cascade = cv2.CascadeClassifier(HAAR_PATH)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        return None
    # choose biggest face
    x, y, w, h = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
    roi = gray[y:y+h, x:x+w]
    roi = cv2.resize(roi, (200, 200))
    return roi

MODEL_DIR = os.path.join(settings.MEDIA_ROOT, "models")
MODEL_FILE = os.path.join(MODEL_DIR, "lbph_model.yml")
LABELS_FILE = os.path.join(MODEL_DIR, "labels.npy")

def ensure_model_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)

def train_lbph(student_id_to_samples: Dict[int, List[str]]) -> Tuple[bool, str]:
    """
    student_id_to_samples: {student_id: [abs_path_img1, abs_path_img2, ...]}
    Saves:
      - LBPH model to MODEL_FILE
      - labels mapping to LABELS_FILE (index -> student_id)
    """
    ensure_model_dir()
    faces = []
    labels = []
    label_index = 0
    label_map = {}  # label_index -> student_id

    for student_id, paths in student_id_to_samples.items():
        for p in paths:
            img = cv2.imread(p)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            roi = detect_face(gray)
            if roi is None:
                continue
            faces.append(roi)
            labels.append(label_index)
        if len(paths) > 0:
            label_map[label_index] = student_id
            label_index += 1

    if len(faces) < 2:
        return False, "Not enough valid face samples to train. Add more samples (2+)."

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    recognizer.save(MODEL_FILE)
    np.save(LABELS_FILE, np.array([label_map.get(i, -1) for i in range(label_index)], dtype=np.int64))
    return True, "Model trained successfully."

@dataclass
class PredictResult:
    student_id: Optional[int]
    confidence: float
    message: str

def predict_lbph(img_bgr: np.ndarray, threshold: float = 65.0) -> PredictResult:
    """
    Lower confidence is better for LBPH.
    We treat confidence <= threshold as matched.
    """
    if not os.path.exists(MODEL_FILE) or not os.path.exists(LABELS_FILE):
        return PredictResult(None, 999.0, "Model not trained yet. Please enroll faces and train model.")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_FILE)
    labels_map = np.load(LABELS_FILE)

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    roi = detect_face(gray)
    if roi is None:
        return PredictResult(None, 999.0, "No face detected. Try again with better lighting and face in center.")

    label, conf = recognizer.predict(roi)
    if label < 0 or label >= len(labels_map):
        return PredictResult(None, float(conf), "Unknown face.")
    student_id = int(labels_map[label])
    if student_id <= 0:
        return PredictResult(None, float(conf), "Unknown face.")

    if conf <= threshold:
        return PredictResult(student_id, float(conf), "Face matched.")
    return PredictResult(None, float(conf), "Face not confident enough. Try again or add more samples.")
