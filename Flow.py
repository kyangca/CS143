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
    RenoSlowStartTransition = 2
    RenoFastRecovery = 3
    # TODO: Generalize Flow so it uses state transitions more effectively.
    RenoTransmit = 4
    #FastSlowStart = 4
    #FastRetransmit = 5
    #FastCA = 6
    #FastFrFr = 7
    RenoCA = 5
    Fast = 6

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
    FAST_ALPHA = 1.0 #TODO: Adopt .75(B/N) estimate Professor Low suggested
    FAST_BASE_RTT = -1 # Use -1 to indicate no Base RTT established yet...

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

    def transition_to_slow_start_part_2(self):
        debug_print("Transitioned to reno state 2")
        self.__state = FlowStates.RenoSlowStartPart2
        debug_print(self.__tcp_sequence_number)
        debug_print(self.__src_id)
        src = self.__controller.devices[self.__src_id]
        src.send_next_packet(self)

    def transition_to_retransmit(self, next_tcp_sequence_number, SSthreshold):
        # If this condition isn't satisfied, then FR worked.
        if (next_tcp_sequence_number > self.__last_ack_number_received):
            print("Retransmitting flow", self.__flow_id, "ssthresh=", SSthreshold)
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
        rtt = ack_packet.get_data_time()
        if(self.FAST_BASE_RTT == -1):
            self.__window_size = self.__window_size + self.FAST_ALPHA
            self.FAST_BASE_RTT = rtt
        else:
            self.__window_size = (self.FAST_BASE_RTT/rtt)*self.__window_size + self.FAST_ALPHA
            if(rtt < self.FAST_BASE_RTT):
                self.FAST_BASE_RTT = rtt

    def receive_ack_reno(self, ack_packet):
        ack_number = ack_packet.get_ack_number()
        if self.__state == FlowStates.RenoSlowStartPart1:
            if self.__last_ack_number_received == ack_number:
                # Can't divide by 2 because we've increased the window size due
                # to received packets.
                self.__SSthreshold = self.__window_size / 2
                self.__window_size = 1.0
                self.__state = FlowStates.RenoSlowStartTransition
                debug_print("slow start transition")
                self.__tcp_sequence_number = ack_number
                # Wait for the packets to timeout.
                transition_time = self.__controller.get_current_time() + \
                                  self.RENO_SLOW_START_TIMEOUT
                self.__state = FlowStates.RenoSlowStartTransition

                self.__controller.add_event(transition_time, self.transition_to_slow_start_part_2, [])
            else:
                self.__window_size += 1
                debug_print(self.__window_size)
                self.__last_ack_number_received = ack_number
            return
        elif self.__state == FlowStates.RenoSlowStartTransition:
            return
        elif self.__state == FlowStates.RenoSlowStartPart2:
            # TODO: handle the case where this doesn't hold.
            #assert (self.__last_ack_number_received != ack_number)
            if self.__window_size < self.__SSthreshold:
                self.__window_size += 1
                self.__lack_ack_number_received = ack_number
            else:
                self.__state = FlowStates.RenoCA
        elif self.__state == FlowStates.RenoCA:
            debug_print(self.__window_size)
            self.__window_size += 1.0 / self.__window_size
        elif self.__state == FlowStates.RenoFastRecovery and \
            self.__num_acks_repeated > self.NUM_ACKS_THRESHOLD - 1 and \
            ack_number > self.__last_ack_number_received:
            self.__window_size = self.__old_window_size / 2.5
            self.__state = FlowStates.RenoCA
            self.__num_acks_repeated = 0

        if self.__last_ack_number_received == ack_number and self.__state != FlowStates.RenoSlowStartPart2:
            self.__num_acks_repeated += 1
            if self.__num_acks_repeated == self.NUM_ACKS_THRESHOLD - 1 and \
                self.__state != FlowStates.RenoFastRecovery:
                # Retransmit.
                self.__fast_recovery_sequence_number = ack_number
                # Store for when we break out of the repetitions.
                self.__old_window_size = self.__window_size
                self.__window_size = self.__window_size / 2 + \
                    self.NUM_ACKS_THRESHOLD - 1
                self.__state = FlowStates.RenoFastRecovery
                print("Fast recovery, flow=", self.__flow_id, "old window size = ", self.__old_window_size)
                self.__tcp_sequence_number -= 1
                # TODO: figure out how long to wait before doing a retransmission.
                transition_time = self.__controller.get_current_time() + 0.5
                # Add an event to go into the retransmit state if necessary.
                self.__controller.add_event(transition_time, self.transition_to_retransmit,
                                            [self.__tcp_sequence_number, self.__old_window_size / 2])
            elif self.__num_acks_repeated > self.NUM_ACKS_THRESHOLD - 1:
                self.__window_size += 1

        if ack_number > self.__tcp_sequence_number:
            self.__tcp_sequence_number = ack_number
            self.__num_acks_repeated = 0
#        if (ack_number != self.__last_ack_number_received):
#            self.__num_acks_repeated = 0
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
        return (self.__last_ack_number_received + self.__window_size <=
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
        assert (self.is_infinite_flow() or self.num_remaining_bytes() > 0)
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

        t = self.__controller.get_current_time()

        return TCPPacket(self.__controller, self.get_src_id(),
                self.get_dst_id(), user_bytes, packet_type,
                sequence_number, ack_number, self.get_flow_id(), t, t)

    def construct_next_data_packet_reno(self):

        if (self.i % 100 == 0):
            print (self.i, "flow=", self.__flow_id, "remaining bytes=", self.num_remaining_bytes(), \
                   self.__state, "window size=", self.__window_size, "state=", self.__state, "ssthresh=", self.__SSthreshold)
        self.i += 1

        if not (self.is_infinite_flow() or self.num_remaining_bytes() > 0):
            return False
        if self.__state == FlowStates.RenoSlowStartTransition:
            # Don't transmit any more packets until all the remaining ones are
            # timed out.
            return False
        # TODO: fix this calculation correct -- how many user bytes can actually
        # be stored in a packet?
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
#            debug_print(self.__tcp_sequence_number)
            self.__tcp_sequence_number += 1

        t = self.__controller.get_current_time()

        return TCPPacket(self.__controller, self.get_src_id(),
                self.get_dst_id(), user_bytes, packet_type,
                sequence_number, ack_number, self.get_flow_id(), t, t)

    def construct_next_ack_packet(self, pack_creation_time):
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
            pack_creation_time,
            self.__controller.get_current_time()
        )
