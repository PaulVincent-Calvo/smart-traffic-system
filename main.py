from classes.road_camera import RoadCamera
from ultralytics import YOLO
from classes.dashboard import Dashboard
import tkinter as tk
import cv2

model = YOLO("vision-mk01.pt") # model initialization

road_camera1 = RoadCamera(
    model = model,
    camera1_index = 0,
    camera2_index = 0
)

root = tk.Tk()
root.title("Vehicle Counter System")
root.geometry("1200x700")

dashboard = Dashboard(root, road_camera1, name = "Road Camera 1") # dashboard inside root

try:
    root.mainloop()
finally:
    road_camera1.release()
    cv2.destroyAllWindows()
