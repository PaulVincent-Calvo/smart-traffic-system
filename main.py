from road_camera import RoadCamera
from ultralytics import YOLO
import time

model = YOLO("vision-mk01.pt")

import time
from road_camera import RoadCamera
from ultralytics import YOLO

model = YOLO("vision-mk01.pt")

rc = RoadCamera(
    model=model,
    camera1_index = 0, # replace indexes
    camera2_index = None,  
)

try:
    while True:
        count = rc.get_vehicle_count()
        print(f"Vehicles: {count}")
        time.sleep(0.5)
finally:
    rc.release()
 