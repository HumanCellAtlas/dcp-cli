from threading import Thread
from . import DEFAULT_THREAD_COUNT

from queue import Queue


class Worker(Thread):
    """ Thread executing tasks from a given tasks queue."""
    def __init__(self, thread_pool):
        Thread.__init__(self)
        self.thread_pool = thread_pool
        self.tasks = self.thread_pool.tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            try:
                func, args, kargs = self.tasks.get()
                func(*args, **kargs)
                self.tasks.task_done()
            except Exception as e:
                # An exception happened in this thread
                self.thread_pool.thread_failure = e
                self.tasks.task_done()


class ThreadPool:
    """ Pool of threads with an associated queue """
    def __init__(self, num_threads=DEFAULT_THREAD_COUNT):
        self.tasks = Queue()
        self.thread_failure = None
        for _ in range(num_threads):
            Worker(self)

    def add_task(self, func, *args, **kargs):
        """ Add a task to the queue """
        self.tasks.put((func, args, kargs))

    def wait_for_completion(self):
        """ Wait for completion of all the tasks in the queue """
        self.tasks.join()
