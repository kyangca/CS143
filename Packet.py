class PacketTypes:
    TCP_DATA = 0
    TCP_ACK = 1

class Packet:
    def __init__(src_id, dst_id, size, packet_type):
        self.__src_id = src_id
        self.__dst_id = dst_id
        self.__size = size
        self.packet_type = packet_type

    def get_size():
        return self.__size

    def get_src_id():
        return self.__src_id

    def get_dst_id():
        return self.__dst_id

    def is_TCP_packet():
        return (self.packet_type == PacketTypes.TCP_DATA or
                self.packet_type == PacketTypes.TCP_ACK)

class TCPPacket(Packet):
    def __init__(self, src_id, dst_id, size, sequence_number, packet_type, flow_id):
        Packet.__init__(src_id, dst_id, size, packet_type)
        self.__sequence_number = sequence_number
        self.__flow_id = flow_id

    def get_flow_id(self):
        return self.__flow_id

    def get_sequence_number(self):
        return self.__sequence_number
