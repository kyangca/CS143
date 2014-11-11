class PacketTypes(object):

    TCP_DATA = 0
    TCP_ACK = 1


class Packet(object):

    def __init__(self, controller, src_id, dst_id, size, packet_type):
        self._controller = controller
        self._src_id = src_id
        self._dst_id = dst_id
        self._size = size
        self.packet_type = packet_type

    def get_size(self):
        return self._size

    def get_src_id(self):
        return self._src_id

    def get_dst_id(self):
        return self._dst_id

    def is_TCP_packet(self):
        return (self.packet_type == PacketTypes.TCP_DATA or
                self.packet_type == PacketTypes.TCP_ACK)


class TCPPacket(Packet):

    def __init__(self, controller, src_id, dst_id, size, packet_type, sequence_number, flow_id):
        super().__init__(controller, src_id, dst_id, size, packet_type)
        self._sequence_number = sequence_number
        self._flow_id = flow_id

    def get_flow_id(self):
        return self._flow_id

    def get_sequence_number(self):
        return self._sequence_number
