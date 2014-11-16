from Packet import TCPPacket
from Packet import PacketTypes

class FlowStates(object):
    RenoSlowStartPart1 = 0
    RenoSlowStartPart2 = 1
    RenoSlowStartTransition = 2
    # TODO: Generalize Flow so it uses state transitions more effectively.
    RenoTransmit = 3

# A flow represents the transfer of data from one host to another.
class Flow(object):

    NUM_ACKS_THRESHOLD = 7
    ACK_PACKET_SIZE = 64
    DATA_MAX_PACKET_SIZE = 1024
    RENO_SLOW_START_TIMEOUT = 2.0

    # num_bytes = None specifies that the flow should continue ad infinitum.
    def __init__(self, controller, src_id, dst_id, flow_id, num_bytes = 0):
        self.__controller = controller
        self.__src_id = src_id
        self.__dst_id = dst_id
        self.__num_remaining_bytes = num_bytes
        self.__sent_bytes = 0
        self.__flow_id = flow_id
        self.__tcp_sequence_number = 0
        self.__last_ack_number_received = 0
        self.__num_acks_repeated = 0
        self.__window_size = 1.0

        self.__SSthreshold = float('inf')
        self.__state = FlowStates.RenoSlowStartPart1

        # Denotes a sequence number to retransmit.
        self.__fast_recovery_sequence_number = None

        # e.g. if we receive TCP data packets of sequence numbers [1,2,3,7,8] then
        # __max_contiguous_sequence_number = 3, __uncounted_sequence_numbers = [7,8]
        self.__max_contiguous_sequence_number = -1 # nothing received yet.
        # TODO: consider using an alternative data structure.
        self.__uncounted_sequence_numbers = {}

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

    def transition_to_slow_start_part_2(self):
        print("Transitioned to reno state 2")
        self.__state = FlowStates.RenoSlowStartPart2
        print (self.__tcp_sequence_number)

    def receive_ack(self, ack_packet):
        ack_number = ack_packet.get_ack_number()
        if (self.__state == FlowStates.RenoSlowStartPart1):
            if (self.__last_ack_number_received == ack_number):
                # Can't divide by 2 because we've increased the window size due to received
                # packets.
                self.__SSthreshold = self.__window_size / 4
                self.__window_size = 1.0
                self.__state = FlowStates.RenoSlowStartTransition
                print("slow start transition")
                self.__tcp_sequence_number = ack_number
                # Wait for the packets to timeout.
                transition_time = self.__controller.get_current_time() + \
                                  self.RENO_SLOW_START_TIMEOUT
                self.__controller.add_event(transition_time, self.transition_to_slow_start_part_2, [])
            else:
                self.__window_size += 1
                self.__last_ack_number_received = ack_number
            return

        elif (self.__state == FlowStates.RenoSlowStartTransition):
            return
        elif (self.__state == FlowStates.RenoSlowStartPart2):
            # TODO: handle the case where this doesn't hold.
            #assert (self.__last_ack_number_received != ack_number)
            if (self.__window_size < self.__SSthreshold):
                self.__window_size += 1
                self.__lack_ack_number_received = ack_number
            else:
                self.__state = FlowStates.RenoTransmit

        if (self.__last_ack_number_received == ack_number):
            self.__num_acks_repeated  += 1
            if (self.__num_acks_repeated == self.NUM_ACKS_THRESHOLD - 1):
                # Retransmit.
                self.__fast_recovery_sequence_number = ack_number
                # Store for when we break out of the repetitions.
                self.__old_window_size = self.__window_size
                self.__window_size = self.__window_size / 2 + self.NUM_ACKS_THRESHOLD - 1
            elif (self.__num_acks_repeated > self.NUM_ACKS_THRESHOLD - 1):
                self.__window_size += 1
            return

        if (self.__num_acks_repeated > self.NUM_ACKS_THRESHOLD - 1):
            self.__window_size = self.__old_window_size / 2
        else:
            self.__window_size += 1.0 / self.__window_size
        self.__num_acks_repeated = 0
        self.__last_ack_number_received = ack_number

    def receive_data(self, data_packet):
        sequence_number = data_packet.get_sequence_number()
        self.__uncounted_sequence_numbers[sequence_number] = True
        while (self.__max_contiguous_sequence_number + 1 in self.__uncounted_sequence_numbers):
            self.__max_contiguous_sequence_number += 1
            self.__uncounted_sequence_numbers.pop(self.__max_contiguous_sequence_number)

    def window_is_full(self):
        return (self.__last_ack_number_received + self.__window_size <= self.__tcp_sequence_number)

    def construct_next_data_packet(self):

        assert (self.is_infinite_flow() or self.num_remaining_bytes() > 0)
        if (self.__state == FlowStates.RenoSlowStartTransition):
            # Don't transmit any more packets until all the remaining ones are timed out.
            return False
        # TODO: fix this calculation correct -- how many user bytes can actually
        # be stored in a packet?
        user_bytes = min(self.DATA_MAX_PACKET_SIZE, self.num_remaining_bytes())
        self.__num_remaining_bytes -= user_bytes
        self.__sent_bytes += user_bytes
        packet_type = PacketTypes.TCP_DATA
        sequence_number = self.__tcp_sequence_number
        ack_number = 0

        if (self.__fast_recovery_sequence_number is not None):
            sequence_number = self.__fast_recovery_sequence_number
            self.__fast_recovery_sequence_number = None
        else:
            sequence_number = self.__tcp_sequence_number
#            print(self.__tcp_sequence_number)
            self.__tcp_sequence_number += 1

        return TCPPacket(self.__controller, self.get_src_id(),
                self.get_dst_id(), user_bytes, packet_type,
                sequence_number, ack_number, self.get_flow_id())

    def construct_next_ack_packet(self):
        sequence_number = 0
        ack_number = self.__max_contiguous_sequence_number + 1
        return TCPPacket(
            self.__controller,
            self.get_dst_id(),
            self.get_src_id(),
            self.ACK_PACKET_SIZE,
            PacketTypes.TCP_ACK,
            sequence_number,
            ack_number,
            self.get_flow_id(),
        )
