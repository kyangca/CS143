from heapq import *

class EventQueue(object):
    
    def __init__(self):
        self.priority_queue = []

    # The given event will be executed in delta_t seconds.
    def add_event(self, t, method, args):
        heappush(self.priority_queue, (t, method, args))

    def pop_event(self):
        return heappop(self.priority_queue)

    def is_empty(self):
        return (len(self.priority_queue) == 0)
