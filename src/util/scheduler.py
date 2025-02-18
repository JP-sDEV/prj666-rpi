import time


class Scheduler:
    def __init__(self, interval, task, run_on_start=False):
        """
        A simple scheduler to run a task at a fixed interval.

        :param interval: Time interval in seconds.
        :param task: Function to execute.
        :param run_on_start: Whether to run the task immediately.
        """
        self.interval = interval
        self.task = task
        self.run_on_start = run_on_start
        self.last_run = 0 if run_on_start else time.time()

    def run(self):
        """Check if it's time to execute the task."""
        current_time = time.time()
        if current_time - self.last_run >= self.interval:
            self.task()
            self.last_run = current_time
