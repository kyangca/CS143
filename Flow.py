from Packet import Packet

# A flow represents the transfer of data from one host to another.
class Flow:
    # num_bytes = None specifies that the flow should continue ad infinitum.
    def __init__(self, controller, src_id, dst_id, flow_id, num_bytes = 0):
        self.__controller = controller
        self.__src_id = src_id
        self.__dst_id = dst_id
        self.__num_remaining_bytes = num_bytes
        self.__sent_bytes = 0
        self.__flow_id = flow_id

    # Returns whether or not the flow should continue ad infinitum.
    def is_infinite_flow(self):
        return self.__num_remaining_bytes is None

    def get_flow_id(self):
        return self.__flow_id

    def num_remaining_bytes(self):
        return self.__num_remaining_bytes

    def get_src_id(self):
        return self.__src_id

    def get_dst_id(self):
        return self.__dst_id

    def construct_next_packet(self):

        assert (self.is_infinite_flow() or self.num_remaining_bytes() > 0)

        # TODO: fix this calculation correct -- how many user bytes can actually
        # be stored in a packet?
        user_bytes = min(1024, self.num_remaining_bytes())
        self.__num_remaining_bytes -= user_bytes
        self.__sent_bytes += user_bytes
        return Packet(self.__controller, self.get_src_id(), self.get_dst_id(), user_bytes, 'flow')
