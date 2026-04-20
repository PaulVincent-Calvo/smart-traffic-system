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

        self._phase_end = 0.0  # absolute timestamp when the current green phase ends

        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        self._thread = threading.Thread(target=self._cycle_loop, daemon=True)
        self._thread.start()

    def _run_green_phase(self, active_road, other_road, is_road1):
        phase_start = time.time()
        phase_end = phase_start + self.default_green_time

        # Reset this road's accumulated green time for the new cycle
        with self._lock:
            if is_road1:
                self._road1_total_green = 0.0
            else:
                self._road2_total_green = 0.0
            self._phase_end = phase_end

        while not self._stop_event.is_set():
            now = time.time()
            elapsed = now - phase_start
            remaining = phase_end - now

            active_count = active_road.get_vehicle_count()
            other_count = other_road.get_vehicle_count()

            # bug fix 1: check green time expiry first so remaining <= 0
            # is never masked by the empty-road checks below
            if remaining <= 0:
                self._commit_green_time(elapsed, is_road1)
                return

            # bug fix 2: force switch if total green time has hit or exceeded max
            total_so_far = self._get_total(is_road1) + elapsed
            if total_so_far >= self.max_green_time:
                self._commit_green_time(elapsed, is_road1)
                return

            # active road is empty, other road has cars — switch
            if active_count == 0 and other_count > 0:
                self._commit_green_time(elapsed, is_road1)
                return

            # both roads are empty, wait
            if active_count == 0 and other_count == 0:
                self._wait(min(remaining, 1.0))
                continue

            # active road is busier than other road; no green time extension
            if active_count >= other_count:
                self._wait(min(remaining, 1.0))
                continue

            # green time less than 20, total green time less than max — extend
            if remaining <= 20:
                if total_so_far < self.max_green_time:
                    max_allowed_end = phase_start + (self.max_green_time - self._get_total(is_road1))
                    new_end = min(phase_end + self.time_adder, max_allowed_end)

                    if new_end > phase_end:
                        phase_end = new_end
                        with self._lock:
                            self._phase_end = phase_end  # expose extension to dashboard

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

    def get_remaining_green_time(self):
        """Return seconds remaining in the current green phase (0 if expired)."""
        with self._lock:
            remaining = self._phase_end - time.time()
        return max(0.0, remaining)

    def get_total_green_time(self):
        with self._lock:
            return self._road1_total_green, self._road2_total_green

    def stop(self):
        self._stop_event.set()
        self._thread.join()