import base64
import binascii

import cv2
import numpy as np


class FaceError(ValueError):
    pass


FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
EYE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")


def decode_frame(data_url):
    if not isinstance(data_url, str) or "," not in data_url:
        raise FaceError("Invalid camera frame.")
    try:
        encoded = data_url.split(",", 1)[1]
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise FaceError("Invalid camera frame.")
    if len(raw) > 4_000_000:
        raise FaceError("Camera frame is too large.")
    frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise FaceError("The camera image could not be read.")
    return frame


def analyze(data_url):
    frame = decode_frame(data_url)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    faces = FACE_CASCADE.detectMultiScale(gray, 1.15, 5, minSize=(100, 100))
    if len(faces) == 0:
        raise FaceError("No face detected. Move closer and improve the lighting.")
    if len(faces) > 1:
        raise FaceError("More than one face detected. Only one person should be visible.")
    x, y, w, h = faces[0]
    face = gray[y : y + h, x : x + w]
    upper = face[: int(h * 0.62), :]
    eyes = EYE_CASCADE.detectMultiScale(upper, 1.1, 5, minSize=(18, 18))

    normalized = cv2.resize(face, (96, 96), interpolation=cv2.INTER_AREA)
    normalized = cv2.equalizeHist(normalized).astype(np.float32) / 255.0
    coeffs = cv2.dct(normalized)[:24, :24].flatten()
    coeffs = coeffs[1:]
    norm = np.linalg.norm(coeffs)
    if norm == 0:
        raise FaceError("The face image has insufficient detail.")
    return coeffs / norm, len(eyes)


def enrollment_template(frames):
    if not isinstance(frames, list) or len(frames) != 3:
        raise FaceError("Exactly three enrollment frames are required.")
    vectors = [analyze(frame)[0] for frame in frames]
    template = np.mean(vectors, axis=0)
    template /= np.linalg.norm(template)
    return template.astype(np.float32)


def verify(template, open_frame, blink_frame, threshold=0.18):
    open_vector, open_eyes = analyze(open_frame)
    blink_vector, blink_eyes = analyze(blink_frame)
    if open_eyes < 1:
        raise FaceError("Open-eyes frame failed. Look at the camera with your eyes open.")
    if blink_eyes >= open_eyes:
        raise FaceError("Blink not detected. Keep still and make a clear blink.")
    probe = open_vector + blink_vector
    probe /= np.linalg.norm(probe)
    distance = float(1.0 - np.dot(template, probe))
    return distance <= threshold, distance
