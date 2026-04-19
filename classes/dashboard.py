import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import threading
import queue
import time


class Dashboard:
    def __init__(self, parent, road_camera, name="Dashboard", traffic_light=None, is_road1=True):
        self.parent = parent
        self.road_camera = road_camera
        self.name = name
        self.traffic_light = traffic_light
        self.is_road1 = is_road1  # True = road1, False = road2; used to read correct green state

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.frame.columnconfigure(0, weight=3)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

        # ── Left: camera feeds ─────────────────────────────────────────────
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

        # ── Right: counts + traffic light status ──────────────────────────
        right_frame = ttk.Frame(self.frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right_frame.columnconfigure(0, weight=1)

        ttk.Label(right_frame, text=name, font=("Arial", 12, "bold")).pack(pady=(10, 20))

        # Vehicle counts
        self.cam1_count_label = ttk.Label(right_frame, text="Camera 1: 0", font=("Arial", 12))
        self.cam1_count_label.pack(pady=5)

        self.cam2_count_label = ttk.Label(right_frame, text="Camera 2: 0", font=("Arial", 12))
        self.cam2_count_label.pack(pady=5)

        self.total_count_label = ttk.Label(right_frame, text="Total: 0", font=("Arial", 14, "bold"))
        self.total_count_label.pack(pady=10)

        ttk.Separator(right_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        # Traffic light indicator
        ttk.Label(right_frame, text="Traffic Light", font=("Arial", 11, "bold")).pack()

        self.light_canvas = tk.Canvas(right_frame, width=60, height=60, bg="#2b2b2b", highlightthickness=0)
        self.light_canvas.pack(pady=8)
        self._light_circle = self.light_canvas.create_oval(10, 10, 50, 50, fill="gray", outline="")

        self.light_label = ttk.Label(right_frame, text="—", font=("Arial", 11, "bold"))
        self.light_label.pack()

        self.countdown_label = ttk.Label(right_frame, text="", font=("Arial", 20, "bold"))
        self.countdown_label.pack(pady=(4, 0))

        ttk.Label(right_frame, text="seconds remaining", font=("Arial", 9)).pack()

        ttk.Separator(right_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        # Green time totals
        ttk.Label(right_frame, text="Total Green Time", font=("Arial", 10)).pack()
        self.green_time_label = ttk.Label(right_frame, text="0s", font=("Arial", 12, "bold"), foreground="green")
        self.green_time_label.pack(pady=4)

        self.photo1 = None
        self.photo2 = None

        # Queue that the background thread pushes processed frames into.
        # maxsize=1 means the bg thread always works on the latest frame —
        # if the UI hasn't consumed the last one yet it gets dropped, avoiding backlog.
        self._frame_queue = queue.Queue(maxsize=1)

        # Background thread: does the heavy cv2/PIL work off the main thread
        self._cam_thread = threading.Thread(target=self._process_frames_loop, daemon=True)
        self._cam_thread.start()

        # Start update loops
        self.update_counts()
        self.update_cameras()  # now just reads from the queue — very cheap
        if self.traffic_light is not None:
            self.update_traffic_light()

    # ── Count polling ──────────────────────────────────────────────────────
    def update_counts(self):
        try:
            camera1 = self.road_camera.get_vehicle_count_cam1()
            camera2 = self.road_camera.get_vehicle_count_cam2()
            total = self.road_camera.get_vehicle_count()

            self.cam1_count_label.config(text=f"Camera 1: {camera1}")
            self.cam2_count_label.config(text=f"Camera 2: {camera2}")
            self.total_count_label.config(text=f"Total: {total}")

        except Exception as e:
            print(f"[{self.name}] Error updating counts: {e}")

        self.parent.after(500, self.update_counts)

    # ── Camera frame processing (background thread) ────────────────────────
    def _process_frames_loop(self):
        """Runs on a background thread. Does the heavy cv2/PIL work and
        pushes ready PhotoImages into the queue for the UI thread to apply."""
        target_interval = 1 / 30  # ~30fps
        while True:
            loop_start = time.time()
            try:
                with self.road_camera._lock:
                    raw1 = self.road_camera.latest_frame1.copy() if self.road_camera.latest_frame1 is not None else None
                    raw2 = self.road_camera.latest_frame2.copy() if self.road_camera.latest_frame2 is not None else None

                photo1 = None
                photo2 = None

                if raw1 is not None:
                    raw1 = cv2.cvtColor(raw1, cv2.COLOR_BGR2RGB)
                    raw1 = cv2.resize(raw1, (500, 280))
                    photo1 = ImageTk.PhotoImage(Image.fromarray(raw1))

                if raw2 is not None:
                    raw2 = cv2.cvtColor(raw2, cv2.COLOR_BGR2RGB)
                    raw2 = cv2.resize(raw2, (500, 280))
                    photo2 = ImageTk.PhotoImage(Image.fromarray(raw2))

                # Drop the old frame if UI hasn't consumed it yet (stay current)
                try:
                    self._frame_queue.put_nowait((photo1, photo2))
                except queue.Full:
                    try:
                        self._frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                    self._frame_queue.put_nowait((photo1, photo2))

            except Exception as e:
                print(f"[{self.name}] Frame processing error: {e}")

            elapsed = time.time() - loop_start
            sleep_time = target_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    # ── Camera feed polling (main/UI thread) ──────────────────────────────
    def update_cameras(self):
        """Runs on the UI thread. Just pulls pre-processed PhotoImages from
        the queue and applies them — no heavy work here."""
        try:
            photo1, photo2 = self._frame_queue.get_nowait()
            if photo1 is not None:
                self.photo1 = photo1
                self.cam1_label.config(image=self.photo1)
            if photo2 is not None:
                self.photo2 = photo2
                self.cam2_label.config(image=self.photo2)
        except queue.Empty:
            pass  # no new frame yet, skip this tick
        except Exception as e:
            print(f"[{self.name}] Error updating cameras: {e}")

        self.parent.after(30, self.update_cameras)

    # ── Traffic light polling ──────────────────────────────────────────────
    def update_traffic_light(self):
        try:
            state = self.traffic_light.get_state()  # "road1_green" or "road2_green"
            is_green = (
                (self.is_road1 and state == "road1_green") or
                (not self.is_road1 and state == "road2_green")
            )

            if is_green:
                self.light_canvas.itemconfig(self._light_circle, fill="#00cc44")
                self.light_label.config(text="GREEN", foreground="green")
                remaining = self.traffic_light.get_remaining_green_time()
                self.countdown_label.config(text=f"{remaining:.0f}", foreground="green")
            else:
                self.light_canvas.itemconfig(self._light_circle, fill="#cc2200")
                self.light_label.config(text="RED", foreground="red")
                self.countdown_label.config(text="—", foreground="gray")

            # Update green time for this road
            road1_time, road2_time = self.traffic_light.get_total_green_time()
            green_time = road1_time if self.is_road1 else road2_time
            self.green_time_label.config(text=f"{green_time:.1f}s")

        except Exception as e:
            print(f"[{self.name}] Error updating traffic light: {e}")

        self.parent.after(300, self.update_traffic_light)