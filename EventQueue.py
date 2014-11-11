from heapq import *

class HeapTuple(object):
    def __init__(self, t, method, args):
        self.t = t
        self.method = method
        self.args = args

    def __lt__(self, heaptuple):
        return self.t < heaptuple.t

    def __gt__(self, heaptuple):
        return self.t > heaptuple.t

    def as_tuple(self):
        return (self.t, self.method, self.args)

class EventQueue(object):
    
    def __init__(self):
        self.priority_queue = []

    # The given event will be executed in delta_t seconds.
    def add_event(self, t, method, args):
        heaptuple = HeapTuple(t, method, args)
        heappush(self.priority_queue, heaptuple)

    def pop_event(self):
        return heappop(self.priority_queue).as_tuple()

    def is_empty(self):
        return (len(self.priority_queue) == 0)
