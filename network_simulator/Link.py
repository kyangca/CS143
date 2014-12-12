class Link(object):
    """Links connect hosts and routers, and carry packets from one end to the
    other. Every link has a specified capacity in bits per second. It is assumed
    that every host and router can process an infinite amount of incoming data
    instantaneously, but outgoing data must sit on a link buffer until the link
    is free. Link buffers are first-in, first-out. Packets that try to enter a
    full buffer will be dropped.

    Attributes:
        __controller: The controller object.
        __left_device: The device on the left side of the link.
        __right_device: The device on the right side of the link.
        __throughput: The throughput in bytes per second.
        __link_delay: The link delay in seconds.
        __buffer_size: The buffer size in bytes.
        __rightward_buffer: The rightward buffer.
        __leftward_buffer: The leftward buffer.
        __link_id: The id of the link.
        __next_leftward_start_transmission_time: The next start transmission
            time for the left.
        __next_rightward_start_transmission_time: The next start transmission
            time for the right.
    """
    def __init__(
        self,
        controller,
        left_device,
        right_device,
        throughput,
        link_delay,
        buffer_size,
        link_id,
    ):
        self.__controller = controller
        self.__left_device = left_device
        self.__right_device = right_device
        self.__throughput = throughput
        self.__link_delay = link_delay
        self.__buffer_size = buffer_size
        self.__rightward_buffer = []
        self.__leftward_buffer = []
        self.__link_id = link_id
        self.__next_leftward_start_transmission_time = 0.0
        self.__next_rightward_start_transmission_time = 0.0

    @staticmethod
    def bytes_in_buffer(buf):
        """Returns the total number of bytes in the buffer."""
        return sum([x.get_size() for x in buf])

    def num_packets_in_buffers(self):
        return len(self.__rightward_buffer) + len(self.__leftward_buffer)

    def get_link_id(self):
        return self.__link_id

    def get_link_delay(self):
        return self.__link_delay

    def get_controller(self):
        return self.__controller

    def buffer_is_full(self, from_device_id, packet_size):
        if (from_device_id == self.__left_device.get_device_id()):
            buf = self.__rightward_buffer
        elif (from_device_id == self.__right_device.get_device_id()):
            buf = self.__leftward_buffer
        else:
            raise Exception("Unknown device")
        return self.__buffer_size - self.bytes_in_buffer(buf) < packet_size

    @staticmethod
    def link_rate_aggregator(values, interval_length):
        """Returns the average link rate in megabits per second (Mbps)."""
        return sum(values) / float(interval_length) * 8.0 / 1000000.0

    def packet_on_wire_handler(self, rightward_direction):
        """Called after the packet is put on the wire (e.g. after 1024 /
        throughput seconds)."""
        receive_time = self.__link_delay + self.__controller.get_current_time()

        if rightward_direction:
            packet = self.__rightward_buffer.pop(0)
            device = self.__right_device
        else:
            packet = self.__leftward_buffer.pop(0)
            device = self.__left_device

#        print("Link.packet_on_wire_handler", packet.get_src_id(), "-->", packet.get_dst_id(), "ack =", packet.get_ack_number(), "seq =", packet.get_sequence_number(), "time =", self.get_controller().get_current_time())

        self.__controller.log(
            "link-rate",
            self.__link_id,
            packet.get_size(),
            values_aggregator=self.link_rate_aggregator,
            ylabel="link rate (Mbps)",
        )

        self.__controller.add_event(
            receive_time,
            device.receive_packet,
            [self, packet],
        )

        # if packet.is_TCP_packet():
        #     print (packet, self.get_link_id(), "sequence # = ", packet.get_sequence_number(),
        #            "ack # = ", packet.get_ack_number(), "t =",
        #            self.get_controller().get_current_time())
        # else:
        #     print ("Running BF", self.get_link_id())

    def opposite_device(self, from_device_id):
        """I assume that routers can know what device is on the other end of the
        router. TODO: Ask Jianchi to make sure this is correct."""
        if from_device_id == self.__left_device.get_device_id():
            return self.__right_device
        elif from_device_id == self.__right_device.get_device_id():
            return self.__left_device
        else:
            raise Exception("Unknown device id.")

    def estimate_cost(self, from_device_id):
        """Returns the estimated amount of time that will be required to send a
        packet from the given attached device across this link. TODO: Ask
        Jianchi how to do correct calculations."""
        if from_device_id == self.__left_device.get_device_id():
            return max(0, self.__next_rightward_start_transmission_time -
                       self.get_controller().get_current_time())
        elif from_device_id == self.__right_device.get_device_id():
            return max(0, self.__next_leftward_start_transmission_time -
                       self.get_controller().get_current_time())
        else:
            raise Exception("Invalid device id.")

    @staticmethod
    def packet_loss_aggregator(values, interval_length):
        return int(sum(values))

    def queue_packet(self, from_device_id, packet):
        """Queues a packet. Returns whether or not the request was successful.

        Args:
            from_device_id: The originating device of the packet.
            packet: The packet object.
        """

        # Update transmission times in case we haven't done things in a while.
        self.__next_rightward_start_transmission_time = \
            max(self.__next_rightward_start_transmission_time,
                self.__controller.get_current_time())
        self.__next_leftward_start_transmission_time = \
            max(self.__next_leftward_start_transmission_time,
                self.__controller.get_current_time())

        self.__controller.log(
            "buffer-occupancy",
            self.__link_id,
            self.num_packets_in_buffers(),
            ylabel="buffer occupancy (pkts)",
        )

        # Figure out direction and buffer.
        if from_device_id == self.__left_device.get_device_id():
            buf = self.__rightward_buffer
            rightward_direction = True
        elif from_device_id == self.__right_device.get_device_id():
            buf = self.__leftward_buffer
            rightward_direction = False
        else:
            raise Exception("Invalid device id")

        # Reject if buffer full.
        if self.__buffer_size - self.bytes_in_buffer(buf) < packet.get_size():
            # Log the packet loss, we are dropping this packet
            self.__controller.log(
                "packet-loss",
                self.__link_id,
                1,
                values_aggregator=self.packet_loss_aggregator,
                ylabel="packet loss (pkts)",
            )
            return False
        else:
            # Log that packet not lost
            self.__controller.log(
                "packet-loss",
                self.__link_id,
                0,
                values_aggregator=self.packet_loss_aggregator,
                ylabel="packet loss (pkts)",
            )

        # Put packet in buffer and add packet on wire event.
        buf.append(packet)
        transmission_time = float(packet.get_size()) / self.get_throughput()
        if rightward_direction:
            # Add an event for when the packet is on the wire.
            self.__next_rightward_start_transmission_time += transmission_time
            self.__next_leftward_start_transmission_time = \
                self.__next_rightward_start_transmission_time + \
                self.get_link_delay()
            self.__controller.add_event(
                self.__next_rightward_start_transmission_time,
                self.packet_on_wire_handler, [True])
        else:
            self.__next_leftward_start_transmission_time += transmission_time
#            if (packet.is_TCP_ack()):
#                print("Link.queue_packet", "sending ack", "transmission_time =", \
#                      self.__next_leftward_start_transmission_time)
            self.__next_rightward_start_transmission_time = \
                self.__next_leftward_start_transmission_time + \
                self.get_link_delay()
            self.__controller.add_event(
                self.__next_leftward_start_transmission_time,
                self.packet_on_wire_handler, [False])

        return True

    def set_left_device(self, device):
        self.__left_device = device

    def set_right_device(self, device):
        self.__right_device = device

    def get_throughput(self):
        return self.__throughput
