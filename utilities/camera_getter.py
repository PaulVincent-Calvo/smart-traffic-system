import cv2

def list_available_cameras(max_index=5):
    """Try indices 0–max_index and return the ones that open successfully."""
    available = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available

print(list_available_cameras())  # [0, 1, 2], 0 kalimitan webcam ng device, yung 1 onwards siguro yung USB camera