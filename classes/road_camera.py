import cv2
import threading
import time

VEHICLE_CLASSES = {"car", "puv", "motorcycle"}

class RoadCamera:
    def __init__(
            self, 
            camera1_index = None, 
            camera2_index = None,
            model = None,
            interface_interval = 5.0  # seconds between inference scans
    ):
        self.camera1 = self.init_camera(camera1_index)
        self.camera2 = self.init_camera(camera2_index)
        self.latest_frame1 = None
        self.latest_frame2 = None
        self.vehicle_count = 0 
        self.interface_interval = interface_interval
        self.model = model
        self.vehicle_count_cam1 = 0
        self.vehicle_count_cam2 = 0

        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        # Separate threads: one for capturing frames, one for inference
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
        self._capture_thread.start()
        self._inference_thread.start()

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

    def _capture_loop(self):
        while not self._stop_event.is_set():
            frame1 = self.read_frame(self.camera1)
            frame2 = self.read_frame(self.camera2)
            with self._lock:
                if frame1 is not None:
                    self.latest_frame1 = frame1
                if frame2 is not None:
                    self.latest_frame2 = frame2

    def _inference_loop(self):
        """Runs every `interface_interval` seconds — does YOLO detection on the latest frames."""
        while not self._stop_event.is_set():
            start = time.time()

            with self._lock:
                frame1 = self.latest_frame1.copy() if self.latest_frame1 is not None else None
                frame2 = self.latest_frame2.copy() if self.latest_frame2 is not None else None

            count1, annotated1 = self.count_vehicles_in_frame(frame1)
            count2, annotated2 = self.count_vehicles_in_frame(frame2)

            with self._lock:
                self.vehicle_count_cam1 = count1
                self.vehicle_count_cam2 = count2
                self.vehicle_count = count1 + count2
                # Store annotated frames so the dashboard shows boxes
                if annotated1 is not None:
                    self.latest_frame1 = annotated1
                if annotated2 is not None:
                    self.latest_frame2 = annotated2

            elapsed = time.time() - start
            sleep_time = self.interface_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def count_vehicles_in_frame(self, frame):
        """Run YOLO on a frame, draw boxes for vehicle classes, return (count, annotated_frame)."""
        if frame is None:
            return 0, None
 
        results = self.model(frame, verbose=False)
        count = 0
        annotated = frame.copy()
 
        for result in results:
            for box, cls_id, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                class_name = self.model.names[int(cls_id)].lower()
                if class_name not in VEHICLE_CLASSES:
                    continue
 
                count += 1
                x1, y1, x2, y2 = map(int, box)
                label = f"{class_name} {conf:.2f}"
 
                # Bounding box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
 
                # Label background
                (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                cv2.rectangle(annotated, (x1, y1 - h - 6), (x1 + w + 4, y1), (0, 255, 0), -1)
 
                # Label text
                cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
 
        return count, annotated

    def get_vehicle_count(self):
        with self._lock:
            return self.vehicle_count

    def get_vehicle_count_cam1(self):
        with self._lock:
            return self.vehicle_count_cam1

    def get_vehicle_count_cam2(self):
        with self._lock:
            return self.vehicle_count_cam2

    def release(self):
        self._stop_event.set()
        self._capture_thread.join()
        self._inference_thread.join()
        for cam in (self.camera1, self.camera2):
            if cam is not None:
                cam.release()