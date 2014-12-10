class PacketTypes(object):
    """Enum for the different packet types."""

    TCP_DATA = 0
    TCP_ACK = 1
    BF_DATA = 2  # Bellman-Ford packet.


class Packet(object):
    """Class that represents a packet in the network simulation.

    Attributes:
        _controller: The controller object.
        _src_id: The id of the source device.
        _dst_id: The id of the destination device.
        _size: The size of the packet in bytes.
        packet_type: The enum value representing the type of packet.
    """

    def __init__(self, controller, src_id, dst_id, size, packet_type):
        self._controller = controller
        self._src_id = src_id
        self._dst_id = dst_id
        self._size = size
        self.packet_type = packet_type

    def __str__(self):
        return "%s -> %s" % (self.get_src_id(), self.get_dst_id())

    def get_size(self):
        return self._size

    def get_src_id(self):
        return self._src_id

    def get_dst_id(self):
        return self._dst_id

    def is_TCP_packet(self):
        return (self.packet_type == PacketTypes.TCP_DATA or
                self.packet_type == PacketTypes.TCP_ACK)

    def is_BF_packet(self):
        return (self.packet_type == PacketTypes.BF_DATA)

    def is_TCP_ack(self):
        return self.packet_type == PacketTypes.TCP_ACK


class TCPPacket(Packet):
    """Class that represents a packet for TCP in the network simulation.

    Attributes:
        _sequence_number: The sequence number used in TCP.
        _ack_number: The acknowledgement number used in TCP.
        _flow_id: The id of the flow for this TCP packet.
    """

    def __init__(self, controller, src_id, dst_id, size, packet_type,
                 sequence_number, ack_number, flow_id, data_time, ack_time):
        super().__init__(controller, src_id, dst_id, size, packet_type)
        assert (self.is_TCP_packet())
        self._sequence_number = sequence_number
        self._ack_number = ack_number
        self._flow_id = flow_id
        self.__data_time = data_time
        self.__ack_time = ack_time

    def get_data_time(self):
        return self.__data_time

    def get_ack_time(self):
        return self.__ack_time

    def get_flow_id(self):
        return self._flow_id

    def get_sequence_number(self):
        return self._sequence_number

    def get_ack_number(self):
        return self._ack_number


class BFPacket(Packet):
    """Class that represents a packet for implementing the Bellman-Ford
    algorithm in the network simulation.

    Attributes:
        _host_id: The id of the host.
        _cost: The cost for use in the Bellman-Ford algorithm.
    """

    def __init__(self, controller, src_id, dst_id, size, host_id, cost):
        super().__init__(controller, src_id, dst_id, size, PacketTypes.BF_DATA)
        self._host_id = host_id
        self._cost = cost

    def get_cost(self):
        return self._cost

    def get_host_id(self):
        return self._host_id
