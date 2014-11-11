from Flow import Flow

class Device(object):
    def __init__(self, controller, links, device_id):
        self._device_id = device_id
        self._controller = controller
        self._links = links

    def get_device_id(self):
        return self._device_id

class Host(Device):
    def __init__(self, controller, links, device_id):
        assert (len(links) == 1)
        super().__init__(controller, links, device_id)
        # _flows is a map from device id values to flow
        # TODO: figure out if we need to include port numbers.
        self._flows = {}

    def get_link(self):
        return self._links[0]

    def add_flow(self, flow_id, flow):
        self._flows[flow_id] = flow

    def send_next_packet(self, flow):
        packet = flow.construct_next_packet()
        self.get_link().queue_packet(self.get_device_id(), packet)
        if (flow.is_infinite_flow() or flow.num_remaining_bytes() > 0):
            #TODO: Use windowing / acknowledgements
            delta_t = 0.1
            method = self.send_next_packet
            args = [flow]
            self._controller.add_event(delta_t + self._controller.get_current_time(), method, args)

    def receive_packet(self, packet):
        if (not packet.is_TCP_packet()):
            raise Exception("Faulty packet received.")

        sequence_number = packet.get_sequence_number()
        sending_device = packet.get_src_id()
        flow_id = packet.get_flow_id()
        if flow_id not in self._flows:
            # Add the new flow to the host's _flows collection.
            # TODO: figure out where to get flow numbers.
            flow = Flow(self._controller, sending_device, self.get_device_id(), flow_id)
            self.add_flow(flow_id, flow)
        # TODO: add acknowledgements.

    # TODO: Bellman / Dijkstra code somewhere.

class Router(Device):
    def __init__(
        self,
        controller,
        links,
        device_id,
        routing_table = {}
    ):
        super().__init__(controller, links, device_id)
        self._routing_table = routing_table

    def receive_packet(self, packet):
        pass

