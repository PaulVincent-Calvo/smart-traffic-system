import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk


class Dashboard:
    def __init__(self, parent, road_camera, name="Dashboard"):
        self.parent = parent
        self.road_camera = road_camera
        self.name = name

        # =========================
        # MAIN CONTAINER (GRID ROOT)
        # =========================
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.frame.columnconfigure(0, weight=3)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

        # =========================
        # LEFT PANEL (CAMERAS)
        # =========================
        left_frame = ttk.Frame(self.frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Camera 1 container
        cam1_frame = ttk.Frame(left_frame)
        cam1_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(cam1_frame, text=f"{name} - Camera 1", font=("Arial", 10, "bold")).pack()

        self.cam1_label = tk.Label(cam1_frame, bg="black")
        self.cam1_label.pack()

        # Camera 2 container
        cam2_frame = ttk.Frame(left_frame)
        cam2_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(cam2_frame, text=f"{name} - Camera 2", font=("Arial", 10, "bold")).pack()

        self.cam2_label = tk.Label(cam2_frame, bg="black")
        self.cam2_label.pack()

        # =========================
        # RIGHT PANEL (COUNTERS)
        # =========================
        right_frame = ttk.Frame(self.frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        right_frame.columnconfigure(0, weight=1)

        ttk.Label(right_frame, text=name, font=("Arial", 12, "bold")).pack(pady=(10, 20))

        self.cam1_count_label = ttk.Label(right_frame, text="Camera 1: 0", font=("Arial", 12))
        self.cam1_count_label.pack(pady=5)

        self.cam2_count_label = ttk.Label(right_frame, text="Camera 2: 0", font=("Arial", 12))
        self.cam2_count_label.pack(pady=5)

        self.total_count_label = ttk.Label(right_frame, text="Total: 0", font=("Arial", 14, "bold"))
        self.total_count_label.pack(pady=20)

        # =========================
        # IMAGE HOLDERS
        # =========================
        self.photo1 = None
        self.photo2 = None

        # start loops
        self.update_counts()
        self.update_cameras()

    # =========================
    # UPDATE COUNTS
    # =========================
    def update_counts(self):
        try:
            camera1 = self.road_camera.get_vehicle_count_cam1()
            camera2 = self.road_camera.get_vehicle_count_cam2()
            total = self.road_camera.get_vehicle_count()

            self.cam1_count_label.config(text=f"Camera 1: {camera1}")
            self.cam2_count_label.config(text=f"Camera 2: {camera2}")
            self.total_count_label.config(text=f"Total: {total}")

        except Exception as e:
            print(f"Error updating dashboard: {e}")

        self.parent.after(500, self.update_counts)

    # =========================
    # UPDATE CAMERAS
    # =========================
    def update_cameras(self):
        try:
            with self.road_camera._lock:
                frame1 = self.road_camera.latest_frame1.copy() if self.road_camera.latest_frame1 is not None else None
                frame2 = self.road_camera.latest_frame2.copy() if self.road_camera.latest_frame2 is not None else None

            if frame1 is not None:
                frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
                frame1 = cv2.resize(frame1, (500, 280))
                self.photo1 = ImageTk.PhotoImage(Image.fromarray(frame1))
                self.cam1_label.config(image=self.photo1)

            if frame2 is not None:
                frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
                frame2 = cv2.resize(frame2, (500, 280))
                self.photo2 = ImageTk.PhotoImage(Image.fromarray(frame2))
                self.cam2_label.config(image=self.photo2)

        except Exception as e:
            print(f"Error updating cameras: {e}")

        self.parent.after(30, self.update_cameras)