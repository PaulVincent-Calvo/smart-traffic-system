from road_camera import RoadCamera
from ultralytics import YOLO
import cv2

model = YOLO("vision-mk01.pt")

rc = RoadCamera(
    model=model,
    camera1_index=0,
    camera2_index=None,  # replace with index when second camera is connected
)

try:
    while True:
        rc.show_cameras()
        print("Vehicle count:", rc.get_vehicle_count())

except KeyboardInterrupt:
    rc.release()
    cv2.destroyAllWindows()
