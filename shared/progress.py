"""Small terminal progress helpers used by the backup and restore engines."""

import sys
import threading


class Spinner:
    """Display a lightweight spinner while a synchronous operation runs."""

    frames = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

    def __init__(self, label):
        self.label = label
        self._stop = threading.Event()
        self._thread = None
        self._enabled = sys.stdout.isatty()

    def start(self):
        if not self._enabled:
            return

        def animate():
            index = 0
            while not self._stop.is_set():
                print(
                    f"\r{self.frames[index % len(self.frames)]} {self.label}",
                    end="",
                    flush=True,
                )
                index += 1
                self._stop.wait(0.1)

        self._thread = threading.Thread(target=animate, daemon=True)
        self._thread.start()

    def stop(self, success=True):
        if self._thread is None:
            marker = "[OK]" if success else "[ERROR]"
            print(f"{marker} {self.label}")
            return
        self._stop.set()
        self._thread.join()
        marker = "[OK]" if success else "[ERROR]"
        print(f"\r{marker} {self.label}\033[K", flush=True)
