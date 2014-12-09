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
    """The global event queue used in the network simulation.

    Attributes:
        priority_queue: The priority queue used for keeping track of all the
            events that occur in the simulation. Since we are using a
            discrete-event model for the network simulation, we need a data
            structure that can efficiently tell us what the next event is.
    """

    def __init__(self):
        self.priority_queue = []

    def add_event(self, t, method, args):
        heaptuple = HeapTuple(t, method, args)
        heappush(self.priority_queue, heaptuple)

    def pop_event(self):
        return heappop(self.priority_queue).as_tuple()

    def is_empty(self):
        return (len(self.priority_queue) == 0)
