from road_camera import RoadCamera
from ultralytics import YOLO
import cv2
from dashboard import Dashboard

# Initialize model and road camera FIRST
model = YOLO("vision-mk01.pt")

rc = RoadCamera(
    model=model,
    camera1_index=1,
    camera2_index=2,
)

# Create dashboard (includes camera display)
dashboard = Dashboard(rc)

# Run tkinter mainloop (this blocks)
try:
    dashboard.root.mainloop()
finally:
    rc.release()
    cv2.destroyAllWindows()
