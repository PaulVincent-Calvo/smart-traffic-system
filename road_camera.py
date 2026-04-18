import cv2
import threading
import time
from ultralytics import YOLO

VEHICLE_CLASSES = {"car", "puv", "motorcycle"}

class RoadCamera:
    def __init__(
            self, 
            green_time = 40, 
            time_adder = 20, 
            max_green_time = 90, 
            camera1_index = None, 
            camera2_index = None,
            model = None,
            interface_interval = 1.0 # seconds between frame scans for vehicle_count
    ):
        self.is_green = False
        self.default_green_time = green_time
        self.time_adder = time_adder
        self.max_green_time = max_green_time
        self.camera1 = self.init_camera(camera1_index)
        self.camera2 = self.init_camera(camera2_index)
        self.vehicle_count = 0 
        self.interface_interval = interface_interval
        self.model = model

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._inference_loop, daemon=True)
        self._thread.start()

    def init_camera(self, camera_index):
        if camera_index is None: 
            return None

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open camera at index {camera_index}")
        return cap

    def read_frame(self, camera):
        if camera is None:
            return None
        ok, frame = camera.read()
        return frame if ok else None

    # ── Vehicle counting ──────────────────────────────────────────────────────

    def count_vehicles_in_frame(self, frame):
        if frame is None:
            return 0
        results = self.model(frame, verbose=False)
        count = 0
        for result in results:
            for cls_id in result.boxes.cls:
                class_name = self.model.names[int(cls_id)].lower()
                if class_name in VEHICLE_CLASSES:
                    count += 1
        return count

    # ── Background inference loop ─────────────────────────────────────────────

    def _inference_loop(self):
        """Runs in a background thread — grabs frames and updates vehicle_count."""
        while not self._stop_event.is_set():
            start = time.time()

            total = 0
            for cam in (self.camera1, self.camera2):
                frame = self.read_frame(cam)
                total += self.count_vehicles_in_frame(frame)

            with self._lock:
                self.vehicle_count = total

            # Sleep for whatever remains of the interval
            elapsed = time.time() - start
            sleep_time = self.inference_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    # ── Public getter (thread-safe) ───────────────────────────────────────────

    def get_vehicle_count(self):
        """Always call this instead of reading self.vehicle_count directly."""
        with self._lock:
            return self.vehicle_count
        
    def release(self):
        """Stop the background thread and release cameras."""
        self._stop_event.set()
        self._thread.join()
        for cam in (self.camera1, self.camera2):
            if cam is not None:
                cam.release()