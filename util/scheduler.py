import uasyncio as asyncio

class AsyncScheduler:
    def __init__(self, interval, task, run_on_start=False):
        """
        A non-blocking scheduler using asyncio.

        :param interval: Time interval in seconds.
        :param task: Async function to execute.
        :param run_on_start: Whether to run the task immediately.
        """
        self.interval = interval
        self.task = task
        self.run_on_start = run_on_start

    async def run(self):
        """Runs the scheduled task at fixed intervals asynchronously."""
        if self.run_on_start:
            await self.task()

        while True:
            await asyncio.sleep(self.interval)
            await self.task()
