from heapq import *
from Controller import Controller

class EventQueue:
    priority_queue = []

    # The given event will be executed in delta_t seconds.
    @classmethod
    def add_event(cls, t, method, args):
        heappush(priority_queue, (t, method, args))

    @classmethod
    def pop_event(cls):
        return heappop(priority_queue)

    @classmethod
    def is_empty(cls):
        return (len(priority_queue) == 0)
