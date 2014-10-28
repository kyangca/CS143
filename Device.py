from Link import Link
from Packet import Packet
from Controller import Controller

class Device:
    def __init__(self, links, device_id):
        self.__device_id = device_id
        self.__links = links

class Host(Device):
    def __init__(self, links, device_id):
        assert (len(links) == 1)
        Device.__init__(self, links, device_id)
        # __flows is a map from device id values to flow
        # TODO: figure out if we need to include port numbers.
        self.__flows = {}

    def get_link(self):
        return self.__links[0]

    def add_flow(self, flow_id, flow):
        self.__flows[flow_id] = flow

    def get_device_id(self):
        return self.__device_id

    def send_next_packet(self, flow):
        packet = flow.construct_next_packet()
        self.get_link().queue_packet(self.get_device_id(), packet)
        if (flow.is_infinite_flow() or flow.num_remaining_bytes() > 0):
            #TODO: Use windowing / acknowledgements
            delta_t = 0.1
            method = self.send_next_packet
            args = [flow]
            EventQueue.add_event(delta_t + Controller.get_current_time(), method, args)

    def receive_packet(self, packet):
        if (not packet.is_TCP_packet()):
            raise Exception("Faulty packet received.")
        sequence_number = packet.get_sequence_number()
        sending_device = packet.get_src_id()
        flow_id = packet.get_flow_id()
        if (not self.__flows.has_key(flow_id)):
            # Add the new flow to the host's __flows collection.
            # TODO: figure out where to get flow numbers.
            flow = Flow(sending_device, self.get_device_id(), flow_id)
            self.add_flow(flow_id, flow)
        # TODO: add acknowledgements.

    # TODO: Bellman / Dijkstra code somewhere.

class Router(Device):
    def __init__(self, links, device_id,
                 routing_table = {}):
        Device.__init__(self, links, device_id)
        self.__routing_table = routing_table

    def receive_packet(self, packet):
        pass

