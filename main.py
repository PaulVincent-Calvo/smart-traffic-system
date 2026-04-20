from classes.road_camera import RoadCamera
from classes.traffic_light import TrafficLight
from classes.dashboard import Dashboard
from ultralytics import YOLO
import tkinter as tk
from tkinter import ttk
import cv2

model = YOLO("vision-mk01.pt")

# One RoadCamera per road, each using a single camera feed
road_camera1 = RoadCamera(
    model=model,
    camera1_index=2,   # physical camera for Road 1
    camera2_index=None
)

road_camera2 = RoadCamera(
    model=model,
    camera1_index=1,   # physical camera for Road 2
    camera2_index=None
)

# Traffic light controller — decides which road gets green time
traffic_light = TrafficLight(
    road1=road_camera1,
    road2=road_camera2,
    green_time=40,
    time_adder=20,
    max_green_time=90
)

root = tk.Tk()
root.title("Vehicle Counter System")
root.geometry("1400x750")

# Two tabs — one dashboard per road
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
notebook.add(tab1, text="Road 1")
notebook.add(tab2, text="Road 2")

dashboard1 = Dashboard(tab1, road_camera1, name="Road 1", traffic_light=traffic_light, is_road1=True)
dashboard2 = Dashboard(tab2, road_camera2, name="Road 2", traffic_light=traffic_light, is_road1=False)

try:
    root.mainloop()
finally:
    traffic_light.stop()
    road_camera1.release()
    road_camera2.release()
    cv2.destroyAllWindows()