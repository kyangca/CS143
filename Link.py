class Link:
    # throughput is in bytes / sec, link_delay in secs,
    # buffer_size is in bytes.
    def __init__(self, left_device, right_device,
                 throughput, link_delay,
                 buffer_size, link_id):
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

    def get_link_delay(self):
        return self.__link_delay

    # Called after the packet is put on the wire (e.g. after 1024 / throughput seconds.
    def packet_on_wire_handler(self, rightward_direction):
        if (rightward_direction):
            packet = self.__rightward_buffer.pop(0)
            t = self.__link_delay + Controller.get_current_time()
            EventQueue.add_event(delay_time + Controller.g, self.__right_device.receive_packet,
                                 [packet])
        else:
            packet = self.__leftward_buffer.pop(0)
            EventQueue.add_event(delay_time, self.__left_device.receive_packet,
                                 [packet])

    # Returns whether or not the request was successful.
    def queue_packet(self, from_device_id, packet):
        self.__next_rightward_start_transmission_time = \
            max(self.__next_rightward_start_transmission_time, Controller.get_current_time())
        self.__next_leftward_start_transmission_time = \
            max(self.__next_leftward_start_transmission_time, Controller.get_current_time())

        buf = None
        rightward_direction = None
        if (from_device_id == self.__left_device.get_id()):
            buf = self.__rightward_buffer
            rightward_direction = True
        elif (from_device_id == self.__right_device.get_id()):
            buf = self.__leftward_buffer
            rightward_direction = False
        else:
            raise Exception("Invalid device id")

        if (self.__buffer_size - self.bytes_in_buffer(buf) > packet.get_size()):
            return False
        buf.append(packet)
        transmission_time = float(packet.get_size()) / self.get_throughput()
        if (rightward_direction):
            # Add an event for when the packet is on the wire.
            self.__next_rightward_start_transmission_time += transmission_time
            self.__next_leftward_start_transmission_time += transmission_time + self.get_link_delay()
            EventQueue.add_event(self.__next_rightward_start_transmission_time,
                                 self.packet_on_wire_handler, [True])
        else:
            self.__next_rightward_start_transmission_time += transmission_time + self.get_link_delay()
            self.__next_leftward_start_transmission_time += transmission_time
            EventQueue.add_event(self.__next_leftward_start_transmission_time,
                                 self.packet_on_wire_handler, [False])
        return True

    def set_left_device(self, device):
        self.__left_device = device

    def set_right_device(self, device):
        self.__right_device = device

    def get_throughput(self):
        return self.__throughput
