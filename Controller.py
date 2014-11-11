import json
from Link import Link
from Device import Host, Router
from Flow import Flow
from EventQueue import EventQueue
from optparse import OptionParser

class Controller(object):

    def __init__(self, options):
        filename = options['filename']
        debug = options['debug']

        self.__filename = filename
        self.__debug = debug
        self.__current_time = 0.0
        self.__event_queue = EventQueue()

        self._links = {}
        self._devices = {}
        self._flows = {}

        with open(filename) as f:
            json_network = json.loads(f.read())

        json_hosts = json_network['hosts']
        json_links = json_network['links']
        json_flows = json_network['flows']
        json_routers = json_network['routers']

        links = {}
        devices = {}

        for json_link in json_links:
            link_id = json_link['id']
            link_throughput = json_link['throughput']
            link_buffer_size = json_link['buffer_size']
            link_delay = json_link['link_delay']

            self._links[link_id] = Link(
                self,
                None,
                None,
                link_throughput,
                link_delay,
                link_buffer_size,
                link_id,
                )

        for json_host in json_hosts:
            host_id = json_host['id']
            host_link_ids = json_host['links']
            host_links = {x: self._links[x] for x in host_link_ids}
            self._devices[host_id] = Host(
                self,
                host_links,
                host_id,
                )

        for json_router in json_routers:
            router_id = json_router['id']
            router_link_ids = json_router['links']
            router_links = {x: self._links[x] for x in router_link_ids}
            bf_freq = json_router['BFfreq']
            # Get the statically generated routing table.
            if ("routing_table" in json_router):
                routing_table = json_router["routing_table"]
            else:
                routing_table = {}
            self._devices[router_id] = Router(
                self,
                router_links,
                router_id,
                bf_freq,
                routing_table,
                )

        # Now add the references to the devices onto the links
        for json_link in json_links:
            link_id = json_link['id']
            link_left_device_id = json_link['left_device_id']
            link_right_device_id = json_link['right_device_id']

            left_device = self._devices[link_left_device_id]
            right_device = self._devices[link_right_device_id]

            self._links[link_id].set_left_device(left_device)
            self._links[link_id].set_right_device(right_device)

        for json_flow in json_flows:
            # Instantiate the flow in the source host and the event in EventQueue
            src_id = json_flow['src_id']
            dst_id = json_flow['dst_id']
            num_bytes = json_flow['num_bytes']
            flow_start = json_flow['start_time']
            flow_id = json_flow['id']
            src_host = self._devices[src_id]
            flow = Flow(
                self,
                src_id,
                dst_id,
                flow_id,
                num_bytes
                )
            src_host.add_flow(flow_id, flow)
            self.__event_queue.add_event(flow_start, src_host.send_next_packet, [flow])

    def add_event(self, *args):
        self.__event_queue.add_event(*args)

    def get_current_time(self):
        return self.__current_time

    def run(self, num_seconds):
        while (not self.__event_queue.is_empty() and self.get_current_time() < num_seconds):
            event = self.__event_queue.pop_event()
            if (self.__debug):
                # TODO: add better debugging here.
                print(event)
            event_time, event_method, event_args = event
            self.__current_time = event_time
            event_method(*event_args)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-f", dest="filename", help="Test json filename (e.g. test0.json)")
    parser.add_option("--debug", action="store_true")
    options, _ = parser.parse_args()
    network_controller = Controller(vars(options))
    network_controller.run(float('inf'))
