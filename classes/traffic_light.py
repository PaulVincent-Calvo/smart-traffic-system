import time
import threading

class TrafficLight:
    def __init__(self, road1, road2, green_time=40, time_adder=20, max_green_time=90):
        self.road1 = road1
        self.road2 = road2

        self.default_green_time = green_time
        self.time_adder = time_adder
        self.max_green_time = max_green_time

        self.road1_is_green = True  # if False, road2 is green

        self._road1_total_green = 0.0
        self._road2_total_green = 0.0

        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        self._thread = threading.Thread(target=self._cycle_loop, daemon=True)
        self._thread.start()

    def _run_green_phase(self, active_road, other_road, is_road1):
        phase_start = time.time()
        phase_end = phase_start + self.default_green_time

        while not self._stop_event.is_set():
            now = time.time()
            elapsed = now - phase_start
            remaining = phase_end - now

            active_count = active_road.get_vehicle_count()
            other_count = other_road.get_vehicle_count()

            # active road is empty other road has cars; switch active road
            if active_count == 0 and other_count > 0:
                self._commit_green_time(elapsed, is_road1)
                return

            # both roads are empty, wait
            if active_count == 0 and other_count == 0:
                self._wait(min(remaining, 1.0))
                continue

            # green tiem ends (no issue)
            if remaining <= 0:
                self._commit_green_time(elapsed, is_road1)
                return

            # active road is busier than other road; no green time extension
            if active_count >= other_count:
                self._wait(min(remaining, 1.0))
                continue

            # green time less than 20, total green time less than max, add more time
            if remaining <= 20:
                total_so_far = self._get_total(is_road1) + elapsed

                if total_so_far < self.max_green_time:
                    max_allowed_end = phase_start + (self.max_green_time - self._get_total(is_road1))
                    new_end = min(phase_end + self.time_adder, max_allowed_end)

                    if new_end > phase_end:
                        phase_end = new_end

            self._wait(min(remaining, 1.0))

        # stop triggered mid-phase
        self._commit_green_time(time.time() - phase_start, is_road1)

    def _cycle_loop(self):
        while not self._stop_event.is_set():
            self.road1_is_green = True
            self._run_green_phase(self.road1, self.road2, is_road1=True)

            if self._stop_event.is_set():
                break

            self.road1_is_green = False
            self._run_green_phase(self.road2, self.road1, is_road1=False)

    def _commit_green_time(self, elapsed, is_road1):
        with self._lock:
            if is_road1:
                self._road1_total_green += elapsed
            else:
                self._road2_total_green += elapsed

    def _get_total(self, is_road1):
        with self._lock:
            return self._road1_total_green if is_road1 else self._road2_total_green

    # ---------------- UTILITY ----------------
    def _wait(self, seconds):
        deadline = time.time() + seconds
        while not self._stop_event.is_set():
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 0.1))

    # ---------------- PUBLIC ----------------
    def get_state(self):
        return "road1_green" if self.road1_is_green else "road2_green"

    def get_total_green_time(self):
        with self._lock:
            return self._road1_total_green, self._road2_total_green

    def stop(self):
        self._stop_event.set()
        self._thread.join()