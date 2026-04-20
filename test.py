import serial
import time
import sys
import cv2
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# Add the smart-traffic-system to path so we can import classes
sys.path.insert(0, str(Path(__file__).parent / "smart-traffic-system"))

from classes.road_camera import RoadCamera
from classes.traffic_light import TrafficLight
from classes.dashboard import Dashboard
from ultralytics import YOLO

# CHANGE THIS to your Arduino port
# Windows example: 'COM3'
# Mac/Linux example: '/dev/ttyUSB0' or '/dev/ttyACM0'
arduino = serial.Serial('COM6', 9600, timeout=1)
time.sleep(2)  # wait for Arduino reset

def set_light(color):
    """Send color command to Arduino"""
    arduino.write((color + '\n').encode())
    print(f"Light set to {color}")

# ============ INITIALIZE TRAFFIC LIGHT SYSTEM ============

# Load YOLO model
print("Loading YOLO model...")
model = YOLO("smart-traffic-system/vision-mk01.pt")

# Create one RoadCamera per road (each with a single camera feed)
print("Initializing road cameras...")
road_camera1 = RoadCamera(
    model=model,
    camera1_index=0,   # physical camera for Road 1
    camera2_index=None
)

road_camera2 = RoadCamera(
    model=model,
    camera1_index=1,   # physical camera for Road 2
    camera2_index=None
)

# Create traffic light controller
print("Initializing traffic light controller...")
traffic_light = TrafficLight(
    road1=road_camera1,
    road2=road_camera2,
    green_time=40,
    time_adder=20,
    max_green_time=90
)

# ============ CREATE GUI WITH DASHBOARD ============

root = tk.Tk()
root.title("Traffic Light System with Arduino Control")
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

# ============ ARDUINO CONTROL LOOP ============

last_state = None
last_switch_time = time.time()
yellow_duration = 3  # seconds to show yellow when switching

def arduino_control_loop():
    """Run in background to control Arduino based on traffic light state"""
    global last_state, last_switch_time
    
    print("Traffic light system started. Arduino connected.")
    set_light('R')  # Start with red
    
    while True:
        try:
            current_state = traffic_light.get_state()
            now = time.time()
            time_since_switch = now - last_switch_time
            
            # State changed: show yellow for a moment before switching
            if current_state != last_state:
                print(f"Phase switch detected: {last_state} → {current_state}")
                set_light('Y')  # Show yellow during transition
                last_switch_time = now
                last_state = current_state
                time.sleep(yellow_duration)  # Keep yellow for 3 seconds
            
            # Send appropriate command based on which road is green
            if current_state == "road1_green":
                set_light('G')
            elif current_state == "road2_green":
                set_light('G')
            else:
                set_light('R')
            
            # Poll every 0.5 seconds for state changes
            time.sleep(0.5)
        except Exception as e:
            print(f"Error in Arduino control loop: {e}")
            time.sleep(1)

# Start Arduino control in background thread
import threading
arduino_thread = threading.Thread(target=arduino_control_loop, daemon=True)
arduino_thread.start()

# ============ START GUI ============

try:
    root.mainloop()
finally:
    print("Shutting down...")
    set_light('R')
    traffic_light.stop()
    road_camera1.release()
    road_camera2.release()
    cv2.destroyAllWindows()
    arduino.close()
    print("System stopped.")