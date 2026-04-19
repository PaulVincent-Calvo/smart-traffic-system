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
            interface_interval = 1.5 # seconds between frame scans for vehicle_count
    ):
        self.is_green = False
        self.default_green_time = green_time
        self.time_adder = time_adder
        self.max_green_time = max_green_time
        self.camera1 = self.init_camera(camera1_index)
        self.camera2 = self.init_camera(camera2_index)
        self.latest_frame1 = None
        self.latest_frame2 = None
        self.vehicle_count = 0 
        self.interface_interval = interface_interval
        self.model = model
        self.vehicle_count_cam1 = 0  # Separate count for camera 1
        self.vehicle_count_cam2 = 0  # Separate count for camera 2

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
    
    def _inference_loop(self):
        while not self._stop_event.is_set():
            start = time.time()

            total = 0
            frames = []

            for i, cam in enumerate((self.camera1, self.camera2)):
                frame = self.read_frame(cam)
                frames.append(frame)

                # Live count - not accumulating, just current vehicles in frame
                if i == 0:
                    self.vehicle_count_cam1 = self.count_vehicles_in_frame(frame)
                else:
                    self.vehicle_count_cam2 = self.count_vehicles_in_frame(frame)

            with self._lock:
                # Live total - sum of current frame detections
                self.vehicle_count = self.vehicle_count_cam1 + self.vehicle_count_cam2
                self.latest_frame1 = frames[0]
                if len(frames) > 1:
                    self.latest_frame2 = frames[1]

            elapsed = time.time() - start
            sleep_time = self.interface_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def show_cameras(self):
        """Call this in your main loop to display camera feeds."""
        with self._lock:
            f1 = self.latest_frame1.copy() if self.latest_frame1 is not None else None
            f2 = self.latest_frame2.copy() if self.latest_frame2 is not None else None

        if f1 is not None:
            cv2.imshow("Camera 1", f1)

        if f2 is not None:
            cv2.imshow("Camera 2", f2)

        cv2.waitKey(1)
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

    def get_vehicle_count(self):
        """Return total vehicle count from both cameras."""
        with self._lock:
            return self.vehicle_count

    def get_vehicle_count_cam1(self):
        """Return vehicle count from camera 1 only."""
        with self._lock:
            return self.vehicle_count_cam1

    def get_vehicle_count_cam2(self):
        """Return vehicle count from camera 2 only."""
        with self._lock:
            return self.vehicle_count_cam2


    def get_vehicle_count(self):
        with self._lock:
            return self.vehicle_count
        
    def release(self):
        self._stop_event.set()
        self._thread.join()
        for cam in (self.camera1, self.camera2):
            if cam is not None:
                cam.release()