class Link(object):
    # throughput is in bytes / sec, link_delay in secs,
    # buffer_size is in bytes.
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
        return sum([x.get_size() for x in buf])

    def get_link_id(self):
        return self.__link_id

    def get_link_delay(self):
        return self.__link_delay

    def get_controller(self):
        return self.__controller

    # Called after the packet is put on the wire (e.g. after 1024 / throughput seconds.
    def packet_on_wire_handler(self, rightward_direction):
        receive_time = self.__link_delay + self.__controller.get_current_time()

        if (rightward_direction):
            packet = self.__rightward_buffer.pop(0)
            device = self.__right_device
        else:
            packet = self.__leftward_buffer.pop(0)
            device = self.__left_device

        self.__controller.add_event(
            receive_time,
            device.receive_packet,
            [self, packet],
        )

        # if (packet.is_TCP_packet()):
        #     print (packet, self.get_link_id(), "sequence # = ", packet.get_sequence_number(),
        #            "ack # = ", packet.get_ack_number(), "t =",
        #            self.get_controller().get_current_time())
        # else:
        #     print ("Running BF", self.get_link_id())

    # I assume that routers can know what device is on the other end of the
    # router.
    # TODO: Ask Jianchi to make sure this is correct.
    def opposite_device(self, from_device_id):
        if (from_device_id == self.__left_device.get_device_id()):
            return self.__right_device
        elif (from_device_id == self.__right_device.get_device_id()):
            return self.__left_device
        else:
            raise Exception("Unknown device id.")

    # Returns the estimated amount of time that will be required to send a
    # packet from the given attached device across this link.
    def estimate_cost(self, from_device_id):
        # TODO: Ask Jianchi how to do correct calculations.
        if (from_device_id == self.__left_device.get_device_id()):
            return max(0, self.__next_rightward_start_transmission_time -
                       self.get_controller().get_current_time())
        elif (from_device_id == self.__right_device.get_device_id()):
            return max(0, self.__next_leftward_start_transmission_time -
                       self.get_controller().get_current_time())
        else:
            raise Exception("Invalid device id.")

    # Returns whether or not the request was successful.
    def queue_packet(self, from_device_id, packet):
        # update transmission times in case we haven't done things in a while
        self.__next_rightward_start_transmission_time = \
            max(self.__next_rightward_start_transmission_time, self.__controller.get_current_time())
        self.__next_leftward_start_transmission_time = \
            max(self.__next_leftward_start_transmission_time, self.__controller.get_current_time())

        # figure out direction and buffer
        if (from_device_id == self.__left_device.get_device_id()):
            buf = self.__rightward_buffer
            rightward_direction = True
        elif (from_device_id == self.__right_device.get_device_id()):
            buf = self.__leftward_buffer
            rightward_direction = False
        else:
            raise Exception("Invalid device id")

        # Reject if buffer full
        if (self.__buffer_size - self.bytes_in_buffer(buf) < packet.get_size()):
            return False

        # Put packet in buffer and add packet on wire event
        buf.append(packet)
        transmission_time = float(packet.get_size()) / self.get_throughput()
        if (rightward_direction):
            # Add an event for when the packet is on the wire.
            self.__next_rightward_start_transmission_time += transmission_time
            self.__next_leftward_start_transmission_time = self.__next_rightward_start_transmission_time + self.get_link_delay()
            self.__controller.add_event(self.__next_rightward_start_transmission_time,
                                 self.packet_on_wire_handler, [True])
        else:
            self.__next_leftward_start_transmission_time += transmission_time
            self.__next_rightward_start_transmission_time = self.__next_leftward_start_transmission_time + self.get_link_delay()
            self.__controller.add_event(self.__next_leftward_start_transmission_time,
                                 self.packet_on_wire_handler, [False])

        return True

    def set_left_device(self, device):
        self.__left_device = device

    def set_right_device(self, device):
        self.__right_device = device

    def get_throughput(self):
        return self.__throughput
