from Flow import Flow
from Packet import BFPacket

class Device(object):
    def __init__(self, controller, links, device_id):
        self._device_id = device_id
        self._controller = controller
        self._links = links

    def get_device_id(self):
        return self._device_id

    def get_links(self):
        return self._links

    def get_controller(self):
        return self._controller

class Host(Device):
    def __init__(self, controller, links, device_id):
        assert (len(links) == 1)
        super().__init__(controller, links, device_id)
        # _flows is a map from device id values to flow
        # TODO: figure out if we need to include port numbers.
        self._flows = {}


    def get_link(self):
        return next(iter(self._links.values()))

    def add_flow(self, flow_id, flow):
        self._flows[flow_id] = flow

    def send_next_packet(self, flow):
        delta_t = 0.01
        method = self.send_next_packet
        args = [flow]
        if (flow.window_is_full()):
            # Wait to send the next packet.
            self._controller.add_event(delta_t + self._controller.get_current_time(), method, args)
            return
        packet = flow.construct_next_data_packet()
        self.get_link().queue_packet(self.get_device_id(), packet)
        if (flow.is_infinite_flow() or flow.num_remaining_bytes() > 0):
            self._controller.add_event(delta_t + self._controller.get_current_time(), method, args)
        else:
            self.get_controller().remove_flow(flow)

    def receive_packet(self, sending_link, packet):
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


        if packet.is_TCP_ack():
            # Update the flow state with the received ack packet.
            self._flows[flow_id].receive_ack(packet)
        else:
            # Update the flow state with the received data packet.
            self._flows[flow_id].receive_data(packet)
            # Construct and send an acknowledgement packet.
            ack_packet_to_send = self._flows[flow_id].construct_next_ack_packet()
            self.get_link().queue_packet(self.get_device_id(), ack_packet_to_send)

        return True

class Router(Device):
    def __init__(
        self,
        controller,
        links,
        device_id,
        bf_freq,
        routing_table = {},
        cost_table = {},
    ):
        super().__init__(controller, links, device_id)
        self._routing_table = routing_table
        self._cost_table = {host: float('inf') for host in routing_table}
        self._bf_freq = bf_freq
        if (bf_freq == 0):
            return
        curtime = controller.get_current_time()
        controller.add_event(curtime + 1.0 / bf_freq, self.start_bellman_ford_round, [])

    def get_link(self, link_id):
        return self._links[link_id]

    # 1) Updates the host's routing table entry with the given cost and link.
    # 2) Sends update BF packets to all adjacent routers except the one which induced this update.
    def bellman_ford_update(self, host_id, cost, mapped_link):
        self._routing_table[host_id] = mapped_link.get_link_id()
        self._cost_table[host_id] = cost
        for link_id, link in self.get_links().items():
            opposite_device = link.opposite_device(self.get_device_id())
            is_host = isinstance(opposite_device, Host)
            if (link == mapped_link or is_host):
                continue
            # TODO: Use correct packet sizes.
            update_packet = BFPacket(self.get_controller(), self.get_device_id(),
                                     None, 1024, host_id, cost)
            link.queue_packet(self.get_device_id(), update_packet)

    def start_bellman_ford_round(self):
        # Queue up the next round.
        controller = self.get_controller()
        curtime = controller.get_current_time()
        controller.add_event(curtime + 1.0 / self._bf_freq, self.start_bellman_ford_round, [])

        for host_id in self._routing_table:
            self._cost_table[host_id] = float('inf')

        for link_id, link in self.get_links().items():
            opposite_device = link.opposite_device(self.get_device_id())
            # TODO: consider adding fields so we don't need to use this.
            if (not isinstance(opposite_device, Host)):
                continue
            host_id = opposite_device.get_device_id()
            cost = link.estimate_cost(self.get_device_id())
            # Update all the other links the cost of the attached host.
            self.bellman_ford_update(host_id, cost, link)
        

    # sending_link is the link which is putting the packet into the router.
    def receive_packet(self, sending_link, packet):
        if packet.is_TCP_packet():
            # Route the packet.
            dst_id = packet.get_dst_id()
            if (not dst_id in self._routing_table):
                # Drop the packet.
                return False
            link_id = self._routing_table[dst_id]
            link = self._links[link_id]
            link.queue_packet(self.get_device_id(), packet)
        elif packet.is_BF_packet():
            host_id = packet.get_host_id()
            host_cost = packet.get_cost() + sending_link.estimate_cost(self.get_device_id())
            if (host_cost < self._cost_table[host_id]):
                self.bellman_ford_update(host_id, host_cost, sending_link)
        else:
            raise Exception("Unsupported packet type")
        return True

