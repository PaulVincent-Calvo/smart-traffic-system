import tkinter as tk
from tkinter import ttk
import threading
import cv2
from PIL import Image, ImageTk


class Dashboard:
    def __init__(self, road_camera):
        self.road_camera = road_camera
        self.root = tk.Tk()
        self.root.title("Vehicle Counter Dashboard")
        self.root.geometry("900x600")
        self.root.resizable(True, True)

        # Style configuration
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        style.configure("Count.TLabel", font=("Arial", 32, "bold"))
        style.configure("Subtitle.TLabel", font=("Arial", 12))

        # Create main container with two columns
        # Left: Camera feeds, Right: Counters
        left_frame = ttk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        right_frame = ttk.Frame(self.root, width=250)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        right_frame.pack_propagate(False)

        # Camera 1 display
        ttk.Label(left_frame, text="Camera 1", style="Subtitle.TLabel").pack()
        self.cam1_label = tk.Label(left_frame, bg="black")
        self.cam1_label.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Camera 2 display
        ttk.Label(left_frame, text="Camera 2", style="Subtitle.TLabel").pack()
        self.cam2_label = tk.Label(left_frame, bg="black")
        self.cam2_label.pack(fill=tk.BOTH, expand=True)

        # Counter section (right side)
        title_label = ttk.Label(right_frame, text="Vehicle Counter", style="Title.TLabel")
        title_label.pack(pady=(0, 30))

        # Camera 1 section
        cam1_frame = ttk.Frame(right_frame)
        cam1_frame.pack(fill=tk.X, pady=15)

        ttk.Label(cam1_frame, text="Camera 1:", style="Subtitle.TLabel").pack(side=tk.LEFT)
        self.cam1_count_label = ttk.Label(cam1_frame, text="0", style="Count.TLabel", foreground="blue")
        self.cam1_count_label.pack(side=tk.RIGHT)

        # Camera 2 section
        cam2_frame = ttk.Frame(right_frame)
        cam2_frame.pack(fill=tk.X, pady=15)

        ttk.Label(cam2_frame, text="Camera 2:", style="Subtitle.TLabel").pack(side=tk.LEFT)
        self.cam2_count_label = ttk.Label(cam2_frame, text="0", style="Count.TLabel", foreground="green")
        self.cam2_count_label.pack(side=tk.RIGHT)

        # Total section
        total_frame = ttk.Frame(right_frame)
        total_frame.pack(fill=tk.X, pady=15)

        ttk.Label(total_frame, text="Total:", style="Subtitle.TLabel").pack(side=tk.LEFT)
        self.total_count_label = ttk.Label(total_frame, text="0", style="Count.TLabel", foreground="red")
        self.total_count_label.pack(side=tk.RIGHT)

        # PhotoImage containers to prevent garbage collection
        self.photo1 = None
        self.photo2 = None

        # Start update loops
        self.update_counts()
        self.update_cameras()

    def update_counts(self):
        """Update the vehicle counts from the RoadCamera instance."""
        try:
            cam1_count = self.road_camera.get_vehicle_count_cam1()
            cam2_count = self.road_camera.get_vehicle_count_cam2()
            total_count = self.road_camera.get_vehicle_count()

            self.cam1_count_label.config(text=str(cam1_count))
            self.cam2_count_label.config(text=str(cam2_count))
            self.total_count_label.config(text=str(total_count))
        except Exception as e:
            print(f"Error updating dashboard: {e}")

        # Schedule next update (every 500ms)
        self.root.after(500, self.update_counts)

    def update_cameras(self):
        """Update camera frames in the dashboard."""
        try:
            # Get frames from road_camera
            with self.road_camera._lock:
                frame1 = self.road_camera.latest_frame1.copy() if self.road_camera.latest_frame1 is not None else None
                frame2 = self.road_camera.latest_frame2.copy() if self.road_camera.latest_frame2 is not None else None

            # Update Camera 1
            if frame1 is not None:
                frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
                frame1 = cv2.resize(frame1, (400, 300))
                img1 = Image.fromarray(frame1)
                self.photo1 = ImageTk.PhotoImage(img1)
                self.cam1_label.config(image=self.photo1)

            # Update Camera 2
            if frame2 is not None:
                frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
                frame2 = cv2.resize(frame2, (400, 300))
                img2 = Image.fromarray(frame2)
                self.photo2 = ImageTk.PhotoImage(img2)
                self.cam2_label.config(image=self.photo2)
        except Exception as e:
            print(f"Error updating cameras: {e}")

        # Schedule next update (every 30ms ~ 30fps)
        self.root.after(30, self.update_cameras)

    def run(self):
        """Start the tkinter main loop."""
        self.root.mainloop()

    def destroy(self):
        """Close the dashboard window."""
        self.root.quit()
        self.root.destroy()


def start_dashboard(road_camera):
    """Start the dashboard in a separate thread."""
    dashboard = Dashboard(road_camera)
    dashboard.run()
