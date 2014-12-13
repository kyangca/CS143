from Packet import PacketTypes
from Packet import TCPPacket

def debug_print(x):
    """Function to use in place of print so that it can easily be disabled."""
    # print(x)
    pass


class FlowStates(object):
    """Enum for the different flow states in the TCP algorithms."""

    RenoSlowStartPart1 = 0
    RenoSlowStartPart2 = 1
    RenoFastRecovery = 2
    # TODO: Generalize Flow so it uses state transitions more effectively.
    RenoCA = 3
    Fast = 4


class Flow(object):
    """A flow represents the transfer of data from one host to another.

    Attributes:
        __controller: The controller object.
        __src_id: The id of the source device.
        __dst_id: The id of the destination device.
        __num_remaining_bytes: The remaining number of bytes to send in this
            flow.
        __sent_bytes: The number of bytes already sent in this flow.
        __flow_id: The id of the flow.
        __tcp_sequence_number: The sequence number as used in TCP.
        __last_ack_number_received: The number of the last acknowledgement
            received.
        __num_acks_repeated: The number of repeated acknowledgements.
        __window_size: The window size.
        __tcp: The TCP algorithm to use specified as a string, e.g. 'reno' or
            'fast'.
    """

    NUM_ACKS_THRESHOLD = 3
    ACK_PACKET_SIZE = 64
    DATA_MAX_PACKET_SIZE = 1024
    RENO_SLOW_START_TIMEOUT = 1.0
    FAST_ALPHA = 0.5
    FAST_BASE_RTT = -1 # -1 indicates no base RTT recorded yet.
    FAST_RECOVERY_RETRANSMIT_TIME = 0.5

    # num_bytes = None specifies that the flow should continue ad infinitum.
    def __init__(self, controller, src_id, dst_id, flow_id, tcp="reno",
            num_bytes = 0):
        self.i = 0
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
        self.__window_start = 0
        self.__tcp = tcp  # TCP algorithm
        debug_print(tcp)

        self.__SSthreshold = float('inf')
        if tcp == "reno":
            self.__state = FlowStates.RenoSlowStartPart1
            debug_print("in reno")
        elif tcp == "fast":
            self.__state = FlowStates.Fast
        else:
            raise NotImplementedError(
                "Unsupported TCP Congestion Control Algorithm")

        # Denotes a sequence number to retransmit.
        self.__fast_recovery_sequence_number = None

        # e.g. if we receive TCP data packets of sequence numbers [1,2,3,7,8]
        # then __max_contiguous_sequence_number = 3,
        # __uncounted_sequence_numbers = [7,8]
        self.__max_contiguous_sequence_number = -1  # Nothing received yet.
        # TODO: Consider using an alternative data structure.
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

    def get_tcp_algorithm(self):
        return self.__tcp

    def transition_to_retransmit(self, next_tcp_sequence_number, SSthreshold):
        # If this condition isn't satisfied, then FR worked.
        if next_tcp_sequence_number > self.__last_ack_number_received:
            # print("Retransmitting flow", self.__flow_id, "ssthresh=",
            #     SSthreshold)
            # Transition into slow start.
            self.__SSthreshold = SSthreshold
            self.__window_size = 1.0
            self.__state = FlowStates.RenoSlowStartPart2
            self.__tcp_sequence_number = self.__last_ack_number_received
            self.__num_acks_repeated = 0

    def receive_ack(self, ack_packet):
        if self.__tcp == "reno":
            self.receive_ack_reno(ack_packet)
        elif self.__tcp == "fast":
            self.receive_ack_fast(ack_packet)
        else:
            raise NotImplementedError(
                "Unsupported TCP Congestion Control Algorithm")

        self.__controller.log(
            "window-size",
            self.__flow_id,
            self.__window_size,
            ylabel="window size (pkts)",
        )

    def receive_ack_fast(self, ack_packet):
        ack_number = ack_packet.get_ack_number()
        self.__last_ack_number_received = ack_number
        # TODO: handle errors.
        if (ack_number > self.__window_start):
            # Slide the window.
            self.__window_start = ack_number
        rtt = self.__controller.get_current_time() - ack_packet.get_data_time()
        if(self.FAST_BASE_RTT == -1):
            self.__window_size = self.__window_size + self.FAST_ALPHA
            self.FAST_BASE_RTT = rtt
        else:
            self.__window_size = (self.FAST_BASE_RTT/rtt)*self.__window_size + \
                self.FAST_ALPHA
            if(self.FAST_BASE_RTT > rtt):
                self.FAST_BASE_RTT = rtt
        print("Flow.receive_ack_fast", "rtt =", rtt, "base_rtt =",
            self.FAST_BASE_RTT, "window size =", self.__window_size, "alpha =",
            self.FAST_ALPHA, "time =", self.__controller.get_current_time())

    def handle_reno_SS1(self, ack_number):
        print("SS1", self.__window_size)
        if self.__last_ack_number_received == ack_number:
            self.__SSthreshold = self.__window_size / 2
            self.__window_size = 1.0
            self.__state = FlowStates.RenoSlowStartPart2
            self.__tcp_sequence_number = ack_number
        else:
            self.__window_size += 1

    def handle_reno_SS2(self, ack_number):
        print ("SS2")
#        assert (ack_number != self.__last_ack_number_received)
        if self.__window_size < self.__SSthreshold:
            self.__window_size += 1
        else:
            self.__state = FlowStates.RenoCA
        print(self.__window_size)

    def handle_duplicate_ack(self, ack_number):
        if self.__last_ack_number_received == ack_number:
            self.__num_acks_repeated += 1
            if self.__num_acks_repeated == self.NUM_ACKS_THRESHOLD - 1:
                # Retransmit.
                self.__fast_recovery_sequence_number = ack_number
                # Store for when we break out of the repetitions.
                self.__old_window_size = self.__window_size
                self.__window_size = self.__window_size / 2 + \
                    self.NUM_ACKS_THRESHOLD - 1
                self.__state = FlowStates.RenoFastRecovery
                # print("Fast recovery, flow=", self.__flow_id,
                #     "old window size = ", self.__old_window_size)
                self.__tcp_sequence_number -= 1
                # TODO: figure out how long to wait before doing a
                # retransmission.
                transition_time = self.__controller.get_current_time() + \
                                  self.FAST_RECOVERY_RETRANSMIT_TIME
                print("set")
                # Add an event to go into the retransmit state if necessary.
                self.__controller.add_event(transition_time,
                    self.transition_to_retransmit, [self.__tcp_sequence_number,
                    self.__old_window_size / 2])

    def handle_reno_FR(self, ack_number):
        print("FR", self.__num_acks_repeated, ack_number)
        if self.__last_ack_number_received == ack_number:
            self.__num_acks_repeated += 1
            if self.__num_acks_repeated > self.NUM_ACKS_THRESHOLD - 1:
                self.__window_size += 1
        elif self.__num_acks_repeated >= self.NUM_ACKS_THRESHOLD - 1:
            self.__window_size = self.__old_window_size / 2.5
            self.__state = FlowStates.RenoCA
            self.__num_acks_repeated = 0

    def handle_reno_CA(self, ack_number):
        print ("CA", self.__window_size)
        self.__window_size += 1.0 / self.__window_size
        self.handle_duplicate_ack(ack_number)

    def receive_ack_reno(self, ack_packet):
        ack_number = ack_packet.get_ack_number()
        if self.__state == FlowStates.RenoSlowStartPart1:
            self.handle_reno_SS1(ack_number)
        elif self.__state == FlowStates.RenoSlowStartPart2:
            self.handle_reno_SS2(ack_number)
        elif self.__state == FlowStates.RenoCA:
            self.handle_reno_CA(ack_number)
        elif self.__state == FlowStates.RenoFastRecovery:
            self.handle_reno_FR(ack_number)

        if ack_number > self.__tcp_sequence_number:
            self.__tcp_sequence_number = ack_number
            self.__num_acks_repeated = 0
        self.__last_ack_number_received = ack_number


    @staticmethod
    def flow_rate_aggregator(values, interval_length):
        """Returns the average flow rate in megabits per second (Mbps)."""
        return sum(values) / float(interval_length) * 8.0 / 1000000.0

    def receive_data(self, data_packet):
        self.__controller.log(
            "flow-rate",
            self.__flow_id,
            data_packet.get_size(),
            values_aggregator=self.flow_rate_aggregator,
            ylabel="flow rate (Mbps)",
        )

        sequence_number = data_packet.get_sequence_number()
        self.__uncounted_sequence_numbers[sequence_number] = True
        while (self.__max_contiguous_sequence_number + 1 in
                self.__uncounted_sequence_numbers):
            self.__max_contiguous_sequence_number += 1
            self.__uncounted_sequence_numbers.pop(
                self.__max_contiguous_sequence_number)

    def window_is_full(self):
        if self.__tcp == "reno":
            return self.window_is_full_reno()
        else:
            return self.window_is_full_fast()

    def window_is_full_reno(self):
        return (self.__last_ack_number_received + self.__window_size <=
            self.__tcp_sequence_number)

    def window_is_full_fast(self):
        return (self.__window_start + self.__window_size <=
            self.__tcp_sequence_number)

    def construct_next_data_packet(self):
        if self.__tcp == "reno":
            return self.construct_next_data_packet_reno()
        elif self.__tcp == "fast":
            return self.construct_next_data_packet_fast()
        else:
            raise NotImplementedError(
                "Unsupported TCP Congestion Control Algorithm")

    def construct_next_data_packet_fast(self):
        if not (self.is_infinite_flow() or self.num_remaining_bytes() > 0):
            return False
        user_bytes = min(self.DATA_MAX_PACKET_SIZE, self.num_remaining_bytes())
        self.__num_remaining_bytes -= user_bytes
        self.__sent_bytes += user_bytes
        packet_type = PacketTypes.TCP_DATA
        sequence_number = self.__tcp_sequence_number
        ack_number = 0

        if self.__fast_recovery_sequence_number is not None:
            sequence_number = self.__fast_recovery_sequence_number
            self.__fast_recovery_sequence_number = None
        else:
            sequence_number = self.__tcp_sequence_number
            self.__tcp_sequence_number += 1

        t = self.__controller.get_current_time()
        return TCPPacket(self.__controller, self.get_src_id(),
                self.get_dst_id(), user_bytes, packet_type,
                         sequence_number, ack_number, self.get_flow_id(), t, t)

    def construct_next_data_packet_reno(self):

        if self.i % 100 == 0:
            # print (self.i, "flow=", self.__flow_id, "remaining bytes=",
            #     self.num_remaining_bytes(), self.__state, "window size=",
            #     self.__window_size, "state=", self.__state, "ssthresh=",
            #     self.__SSthreshold)
            pass
        self.i += 1

        if not (self.is_infinite_flow() or self.num_remaining_bytes() > 0):
            return False
        user_bytes = min(self.DATA_MAX_PACKET_SIZE, self.num_remaining_bytes())
        self.__num_remaining_bytes -= user_bytes
        self.__sent_bytes += user_bytes
        packet_type = PacketTypes.TCP_DATA
        sequence_number = self.__tcp_sequence_number
        ack_number = 0

        if self.__fast_recovery_sequence_number is not None:
            sequence_number = self.__fast_recovery_sequence_number
            self.__fast_recovery_sequence_number = None
        else:
            sequence_number = self.__tcp_sequence_number
            self.__tcp_sequence_number += 1
        t = self.__controller.get_current_time()
        return TCPPacket(self.__controller, self.get_src_id(),
                self.get_dst_id(), user_bytes, packet_type,
                sequence_number, ack_number, self.get_flow_id(), t, t)

    def construct_next_ack_packet(self, data_pack_time):
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
            data_pack_time,
            self.__controller.get_current_time()
        )
