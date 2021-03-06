from Flow import Flow
from Packet import BFPacket

class Device(object):
    """The Device class that Host and Router derives from.

    Attributes:
        device_id: The id of the device, usually a character representing the
            class and a number, e.g. H1 for host 1 and R1 for router 1.
        controller: The controller object.
        links: The links of the object.
    """

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
    """Hosts represent individual endpoint computers, like desktop computers or
    servers.

    Attributes:
        _flows: The set of flows for this host.
    """

    def __init__(self, controller, links, device_id):
        assert (len(links) == 1)
        super().__init__(controller, links, device_id)
        # _flows is a map from device id values to flow
        self._flows = {}

    def get_link(self):
        return next(iter(self._links.values()))

    def add_flow(self, flow_id, flow):
        self._flows[flow_id] = flow

    def send_next_packet(self, flow):
        if (not self.get_link().buffer_is_full(self.get_device_id(), 1024) \
            and not flow.window_is_full()):
            packet = flow.construct_next_data_packet()
            # This operation fails if e.g. we're waiting for the network to
            # clear.
            if packet:
                self.get_link().queue_packet(self.get_device_id(), packet)
                if (not flow.is_infinite_flow() and flow.num_remaining_bytes()
                        <= 0):
                    self.get_controller().remove_flow(flow)
                    # Don't queue up any more packets.
                    return
        t = self.get_controller().get_current_time() + \
            (1024.0 / self.get_link().get_throughput())
        self.get_controller().add_event(t, self.send_next_packet, [flow])


    def receive_packet(self, sending_link, packet):
        if not packet.is_TCP_packet():
            raise Exception("Faulty packet received.")

        sequence_number = packet.get_sequence_number()
        sending_device = packet.get_src_id()
        flow_id = packet.get_flow_id()
        if flow_id not in self._flows:
            # Add the new flow to the host's _flows collection.
            flow = Flow(self._controller, sending_device, self.get_device_id(),
                flow_id)
            self.add_flow(flow_id, flow)

        if packet.is_TCP_ack():
            # Update the flow state with the received ack packet.
            self._flows[flow_id].receive_ack(packet)
        else:
            # Update the flow state with the received data packet.
            self._flows[flow_id].receive_data(packet)
            # Construct and send an acknowledgement packet.
            ack_packet_to_send = self._flows[flow_id] \
                .construct_next_ack_packet(packet.get_data_time())
            assert(self.get_link().queue_packet(self.get_device_id(),
                ack_packet_to_send))
        return True


class Router(Device):
    """Routers represent the network equipment that sits between hosts.

    Attributes:
        _routing_table: The routing table.
        _cost_table: The cost table.
        _bf_freq: The frequency used in the Bellman-Ford algorithm.
    """

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
        if bf_freq == 0:
            return
        curtime = controller.get_current_time()
        controller.add_event(curtime + 1.0 / bf_freq,
            self.start_bellman_ford_round, [])

    def get_link(self, link_id):
        return self._links[link_id]

    def bellman_ford_update(self, host_id, cost, mapped_link):
        """
        1) Updates the host's routing table entry with the given cost and link.
        2) Sends update BF packets to all adjacent routers except the one which
        induced this update.
        """
        self._routing_table[host_id] = mapped_link.get_link_id()
        self._cost_table[host_id] = cost
        for link_id, link in self.get_links().items():
            opposite_device = link.opposite_device(self.get_device_id())
            is_host = isinstance(opposite_device, Host)
            if link == mapped_link or is_host:
                continue
            update_packet = BFPacket(self.get_controller(),
                self.get_device_id(), None, 1024, host_id, cost)
            link.queue_packet(self.get_device_id(), update_packet)

    def start_bellman_ford_round(self):
        # Queue up the next round.
        controller = self.get_controller()
        curtime = controller.get_current_time()
        controller.add_event(curtime + 1.0 / self._bf_freq,
            self.start_bellman_ford_round, [])

        for host_id in self._routing_table:
            self._cost_table[host_id] = float('inf')

        for link_id, link in self.get_links().items():
            opposite_device = link.opposite_device(self.get_device_id())
            if not isinstance(opposite_device, Host):
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
            if not dst_id in self._routing_table:
                # Drop the packet.
                return False
            link_id = self._routing_table[dst_id]
            link = self._links[link_id]
            link.queue_packet(self.get_device_id(), packet)
        elif packet.is_BF_packet():
            host_id = packet.get_host_id()
            host_cost = packet.get_cost() + sending_link.estimate_cost(
                self.get_device_id())
            if host_cost < self._cost_table[host_id]:
                self.bellman_ford_update(host_id, host_cost, sending_link)
        else:
            raise Exception("Unsupported packet type")
        return True
